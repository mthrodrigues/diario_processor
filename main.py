import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from scanner import (
    listar_pdfs,
    extrair_diario_id,
    extrair_data_publicacao
)

from config import get_postgres_config

from taxonomy.entity_taxonomy import (

    PESSOA,
    EMPRESA,
    ORGAO_PUBLICO,

    AGENTE_PUBLICO,
    FORNECEDOR,
    ORGAO_CONTRATANTE
)

from extractor import extrair_texto
from parser import segmentar_publicacoes
from processor import extrair_metadados_bloco

from infra.db.connection import postgres_connection

from infra.db.repositories.publicacao_repository import (
    PublicacaoRepository
)

from infra.db.repositories.evento_repository import (
    EventoRepository
)

from infra.db.repositories.entity_repository import (
    EntityRepository
)

from infra.db.repositories.entity_relationship_repository import (
    EntityRelationshipRepository
)

from infra.db.repositories.timeline_repository import (
    TimelineRepository
)

from infra.db.repositories.institutional_event_outbox_repository import (
    InstitutionalEventOutboxRepository
)

from events import extrair_eventos_bloco

from taxonomy.relation_resolver import (
    resolver_relacao_evento
)

from taxonomy.event_taxonomy import (

    NOMEACAO,
    EXONERACAO,

    NOMEADO_EM,
    EXONERADO_DE
)

from canonical_event_builder import (
    build_institutional_event
)

from consolidador_processos import consolidar_postgres
from consolidador_contratos import consolidar_postgres as consolidar_contratos_postgres


def _emitir_audit(prefix, pdf_path=None, extra=None):
    cfg = get_postgres_config()
    try:
        repo_root = Path(__file__).resolve().parent
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
        branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception as exc:
        commit_sha = f"ERR:{exc}"
        branch_name = f"ERR:{exc}"

    payload = {
        "commit_sha": commit_sha,
        "branch": branch_name,
        "arquivo_processado": str(pdf_path) if pdf_path is not None else None,
        "pid": os.getpid(),
        "db": cfg.db,
        "host": cfg.host,
        "schema": cfg.schema,
    }
    if extra:
        payload.update(extra)
    print(f"[AUDIT][{prefix}]", payload)


def _mostrar_estado_publicacao(conn, pdf_path, numero_bloco):
    schema = get_postgres_config().schema
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                contratante,
                contratante_normalizado
            FROM {schema}.publicacoes
            WHERE arquivo_path = %s
              AND numero_bloco = %s
            """,
            (str(pdf_path), numero_bloco),
        )
        print("[AUDIT][SELECT_RESULT]", cursor.fetchall())


def run():

    _emitir_audit("RUN_START")
    print("Iniciando Diário Processor...\n")

    with postgres_connection() as conn:
        repository = PublicacaoRepository(conn)

        evento_repository = EventoRepository(conn)

        entity_repository = EntityRepository(conn)

        relationship_repository = (
            EntityRelationshipRepository(conn)
        )

        timeline_repository = TimelineRepository(conn)

        outbox_repository = (
            InstitutionalEventOutboxRepository(conn)
        )

        # =================================================
        # PDFs
        # =================================================

        pdfs = listar_pdfs()

        print(f"Total de PDFs encontrados: {len(pdfs)}\n")

        novos = 0
        ignorados = 0

        REPROCESSAR_TUDO = True

        # =================================================
        # LOOP PDFs
        # =================================================

        for pdf in pdfs:

            try:

                # =============================================
                # INCREMENTALIDADE
                # =============================================

                if (
                    not REPROCESSAR_TUDO
                    and repository.ja_processado(pdf)
                ):

                    ignorados += 1

                    continue

                diario_id = extrair_diario_id(pdf)

                _emitir_audit("PROCESSANDO_PDF", pdf, {"diario_id": diario_id})
                print("\n================================================")
                print(f"Processando diário {diario_id}")
                print(f"Arquivo: {pdf}")
                print("================================================")

                # =============================================
                # TEXTO
                # =============================================

                texto = extrair_texto(pdf)

                # =============================================
                # DATA CONTEXTUAL
                # =============================================

                data_publicacao = (
                    extrair_data_publicacao(texto)
                )

                print(
                    "DATA PUBLICACAO EXTRAIDA:",
                    data_publicacao
                )

                # =============================================
                # SEGMENTAÇÃO
                # =============================================

                blocos = segmentar_publicacoes(texto)

                print(f"\nBlocos encontrados: {len(blocos)}")

                # =============================================
                # LOOP BLOCOS
                # =============================================

                for i, bloco in enumerate(
                    blocos,
                    start=1
                ):

                    print(f"\n--- BLOCO {i} ---")

                    metadados = extrair_metadados_bloco(
                        bloco
                    )

                    # ================================
                    # Enriquecimento Contextual (Regra 001)
                    # ================================
                    # Se aplicável, herda contratante institucional do bloco anterior
                    try:
                        from contextual_enrichment import aplicar_regra_001_heranca_contratante

                        prev_block_text = previous_bloco if 'previous_bloco' in locals() else None
                        prev_metadados = previous_metadados if 'previous_metadados' in locals() else None
                        prev_num = previous_numero if 'previous_numero' in locals() else None
                        curr_num = i

                        updated_metadados, applied, audit = aplicar_regra_001_heranca_contratante(
                            prev_block_text,
                            prev_metadados,
                            prev_num,
                            bloco,
                            metadados,
                            curr_num,
                            str(pdf)
                        )

                        _emitir_audit(
                            "ETAPA2_EC",
                            pdf,
                            {
                                "bloco": i,
                                "applied": applied,
                                "criterion": audit.get("criterion") if audit else None,
                                "contratante": updated_metadados.get("contratante") if updated_metadados else None,
                                "contratante_normalizado": updated_metadados.get("contratante_normalizado") if updated_metadados else None,
                            },
                        )

                        if applied:
                            metadados = updated_metadados
                    except Exception:
                        # silenciar falhas do enriquecimento para não interromper o pipeline
                        pass

                    # 保存前保留当前 bloco作为 "previous" para próxima iteração
                    previous_bloco = bloco
                    previous_metadados = metadados
                    previous_numero = i

                    # =========================================
                    # EVENTOS
                    # =========================================

                    eventos = extrair_eventos_bloco(
                        metadados,
                        bloco,
                        diario_id,
                        i
                    )

                    print("\nEVENTOS ENCONTRADOS:")

                    # =========================================
                    # LOOP EVENTOS
                    # =========================================

                    for evento in eventos:

                        print(evento)

                        tipo_evento = evento.get("tipo_evento")

                        # =====================================
                        # SALVA EVENTO
                        # =====================================

                        evento_id = (
                            evento_repository.salvar_evento(
                                evento,
                                data_publicacao=data_publicacao
                            )
                        )

                        print(
                            "EVENTO SALVO:",
                            evento_id
                        )

                        # =====================================
                        # EVENTO CANÔNICO
                        # =====================================

                        canonical_event = (
                            build_institutional_event(
                                evento,
                                evento_id
                            )
                        )

                        try:

                            if canonical_event:

                                outbox_repository.publish(
                                    canonical_event
                                )

                                print(
                                    "EVENTO CANONICO PUBLICADO"
                                )

                        except Exception as e:

                            print(
                                "Erro ao publicar evento:",
                                e
                            )

                        # =====================================
                        # AGENTE
                        # =====================================

                        agente_nome = (
                            evento.get("agente", {})
                            .get("nome")
                        )

                        if agente_nome:

                            entidade_pessoa_id = (
                                entity_repository.obter_ou_criar(
                                    PESSOA,
                                    agente_nome
                                )
                            )

                            evento_repository.relacionar_entidade(
                                evento_id,
                                entidade_pessoa_id,
                                AGENTE_PUBLICO
                            )

                            # =================================
                            # RELAÇÃO PESSOA → ÓRGÃO
                            # =================================

                            orgao_nome = evento.get("orgao")

                            if orgao_nome:

                                entidade_orgao_id = (
                                    entity_repository.obter_ou_criar(
                                        ORGAO_PUBLICO,
                                        orgao_nome
                                    )
                                )

                                tipo_relacao = (
                                    resolver_relacao_evento(
                                        evento.get(
                                            "tipo_evento"
                                        )
                                    )
                                )

                                relationship_repository.criar_relacao(

                                    entidade_pessoa_id,
                                    entidade_orgao_id,

                                    tipo_relacao,

                                    diario_id=diario_id,

                                    data_publicacao=(
                                        data_publicacao
                                    ),

                                    evento_id=evento_id
                                )

                        # =========================================
                        # TIMELINE FUNCIONAL
                        # =========================================

                        if tipo_evento == NOMEACAO:

                            timeline_repository.abrir_vinculo(

                                entidade_pessoa_id,
                                entidade_orgao_id,

                                "LOTACAO",

                                data_publicacao,

                                evento_id
                            )

                        elif tipo_evento == EXONERACAO:

                            timeline_repository.fechar_vinculo(

                                entidade_pessoa_id,
                                entidade_orgao_id,

                                data_publicacao,

                                evento_id
                            )

                        # =====================================
                        # ÓRGÃO
                        # =====================================

                        orgao_nome = evento.get("orgao")

                        if orgao_nome:

                            entidade_id = (
                                entity_repository.obter_ou_criar(
                                    ORGAO_PUBLICO,
                                    orgao_nome
                                )
                            )

                            evento_repository.relacionar_entidade(
                                evento_id,
                                entidade_id,
                                ORGAO_CONTRATANTE
                            )

                        # =====================================
                        # EMPRESA
                        # =====================================

                        empresa_nome = (
                            evento.get(
                                "entidade_destino",
                                {}
                            ).get("nome")
                        )

                        if empresa_nome:

                            entidade_id = (
                                entity_repository.obter_ou_criar(
                                    EMPRESA,
                                    empresa_nome
                                )
                            )

                            evento_repository.relacionar_entidade(
                                evento_id,
                                entidade_id,
                                FORNECEDOR
                            )

                    # =========================================
                    # DEBUG METADADOS
                    # =========================================

                    print(
                        f"Tipo identificado: "
                        f"{metadados['tipo']}"
                    )

                    print(
                        f"Processo identificado: "
                        f"{metadados['processo']}"
                    )

                    print(
                        f"Processo normalizado: "
                        f"{metadados['processo_normalizado']}"
                    )

                    print(
                        f"Contrato identificado: "
                        f"{metadados['contrato']}"
                    )

                    print(
                        f"Fornecedor identificado: "
                        f"{metadados['fornecedor']}"
                    )

                    print(
                        f"Fornecedor normalizado: "
                        f"{metadados['fornecedor_normalizado']}"
                    )

                    print(
                        f"Contratante identificado: "
                        f"{metadados['contratante']}"
                    )

                    print(
                        f"Contratante normalizado: "
                        f"{metadados['contratante_normalizado']}"
                    )

                    print(
                        f"Vigência identificada: "
                        f"{metadados['vigencia']}"
                    )

                    print(
                        f"Objeto identificado: "
                        f"{metadados['objeto']}"
                    )

                    print(
                        f"CNPJ identificado: "
                        f"{metadados['cnpj']}"
                    )

                    if metadados["valores"]:

                        print(
                            f"Valores encontrados: "
                            f"{metadados['valores'][:5]}"
                        )

                    else:

                        print(
                            "Nenhum valor encontrado."
                        )

                    print(
                        f"Valor principal identificado: "
                        f"{metadados['valor_principal']}"
                    )

                    # =========================================
                    # SALVA PUBLICAÇÃO
                    # =========================================

                    _emitir_audit(
                        "ETAPA3_BEFORE_REPOSITORY",
                        pdf,
                        {
                            "bloco": i,
                            "contratante": metadados.get("contratante"),
                            "contratante_normalizado": metadados.get("contratante_normalizado"),
                            "metadados": metadados,
                        },
                    )

                    repository.salvar_publicacao(

                        diario_id,
                        i,
                        pdf,
                        bloco,

                        metadados["tipo"],
                        metadados["processo"],
                        metadados["contrato"],

                        metadados["contratante"],
                        metadados["fornecedor"],

                        metadados["cnpj"],
                        metadados["valores"],

                        metadados["valor_principal"],


                        metadados["vigencia"],
                        metadados["objeto"],

                        metadados[
                            "fornecedor_normalizado"
                        ],

                        metadados[
                            "contratante_normalizado"
                        ],

                        metadados[
                            "processo_normalizado"
                        ],

                        data_publicacao=data_publicacao,
                        contrato_normalizado=metadados[
                            "contrato_normalizado"
                        ],
                    )

                novos += 1

                conn.commit()
                _emitir_audit("ETAPA6_AFTER_COMMIT", pdf, {"bloco": i})
                _mostrar_estado_publicacao(conn, pdf, i)

            except Exception as e:

                conn.rollback()

                import traceback

                print(
                    f"Erro ao processar {pdf}: {e}"
                )

                traceback.print_exc()

        # =========================================
        # CAMADA DE CONSOLIDAÇÃO
        # =========================================

        print("\n========================================")
        print("Iniciando consolidação do domínio...")
        print("========================================")

        # A persistência das evidências já foi confirmada. A consolidação
        # possui uma transação própria e não pode desfazer esses commits.
        conn.commit()

        try:
            consolidar_postgres(
                conn,
                schema=get_postgres_config().schema,
            )
            conn.commit()
            print("Consolidação de processos concluída.")
        except Exception:
            conn.rollback()
            raise

        try:
            consolidar_contratos_postgres(
                conn,
                schema=get_postgres_config().schema,
            )
            conn.commit()
            print("Consolidação de contratos concluída.")
        except Exception:
            conn.rollback()
            raise

        print("\n========================================")
        print("Resumo da execução:")
        print(f"Novos processados: {novos}")
        print(
            f"Ignorados (já existentes): "
            f"{ignorados}"
        )
        print("========================================")

    target_pdf_path = Path("C:/automacoes/diario_bot/pdfs/2026/07/diario_3388.pdf")
    target_numero_bloco = 5
    _emitir_audit("ETAPA7_FINAL_SELECT", target_pdf_path, {"bloco": target_numero_bloco})
    with postgres_connection() as conn_final:
        _mostrar_estado_publicacao(conn_final, target_pdf_path, target_numero_bloco)


if __name__ == "__main__":

    run()
