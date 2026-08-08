import sys
import time

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


def run():

    inicio_total = time.time()

    print("--------------------------------------------------")
    print("Iniciando Diário Processor")

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

        print(f"PDFs encontrados: {len(pdfs)}")
        print("--------------------------------------------------\n")

        novos = 0
        ignorados = 0
        erros = 0

        REPROCESSAR_TUDO = True

        # =================================================
        # LOOP PDFs
        # =================================================

        for idx, pdf in enumerate(pdfs, start=1):

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

                inicio_pdf = time.time()

                print(f"[{idx}/{len(pdfs)}] Processando diário {diario_id}")
                print(f"  Arquivo: {pdf.name}")

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

                # =============================================
                # SEGMENTAÇÃO
                # =============================================

                blocos = segmentar_publicacoes(texto)

                print(f"  Blocos: {len(blocos)}")

                # =============================================
                # LOOP BLOCOS
                # =============================================

                total_eventos = 0
                ec_aplicacoes = 0
                ec_criterio = None

                for i, bloco in enumerate(
                    blocos,
                    start=1
                ):

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

                        if applied:
                            metadados = updated_metadados
                            ec_aplicacoes += 1
                            ec_criterio = audit.get("criterion") if audit else None
                            print(
                                f"  EC aplicada | diario_{diario_id} | "
                                f"bloco {prev_num} → {curr_num} | "
                                f"critério {ec_criterio}"
                            )
                    except Exception:
                        # silenciar falhas do enriquecimento para não interromper o pipeline
                        pass

                    # preserve bloco atual como "previous" para próxima iteração
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

                    # =========================================
                    # LOOP EVENTOS
                    # =========================================

                    for evento in eventos:

                        total_eventos += 1

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

                        except Exception as e:

                            print(
                                f"  [ERRO] Publicar evento canônico | "
                                f"diário {diario_id} bloco {i}: {e}"
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
                    # SALVA PUBLICAÇÃO
                    # =========================================

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

                duracao = time.time() - inicio_pdf
                ec_info = (
                    f"{ec_aplicacoes} aplicação(ões) (critério {ec_criterio})"
                    if ec_aplicacoes
                    else "nenhuma aplicação"
                )
                print(f"  Eventos: {total_eventos}")
                print(f"  EC: {ec_info}")
                print(f"  Concluído em: {duracao:.1f}s\n")

            except Exception as e:

                conn.rollback()

                erros += 1

                import traceback

                print(
                    f"  [ERRO] diário {diario_id} | bloco {i if 'i' in locals() else '?'}: {e}"
                )

                traceback.print_exc()

        # =========================================
        # CAMADA DE CONSOLIDAÇÃO
        # =========================================

        print("--------------------------------------------------")
        print("Consolidação")
        print("--------------------------------------------------")

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

        duracao_total = time.time() - inicio_total
        minutos = int(duracao_total // 60)
        segundos = duracao_total % 60

        print()
        print("--------------------------------------------------")
        print("Resumo da execução")
        print("--------------------------------------------------")
        print(f"PDFs encontrados: {len(pdfs)}")
        print(f"Processados:      {novos}")
        print(f"Ignorados:        {ignorados}")
        print(f"Erros:            {erros}")
        if minutos:
            print(f"Tempo total:      {minutos}m {segundos:.0f}s")
        else:
            print(f"Tempo total:      {duracao_total:.1f}s")
        print("--------------------------------------------------")


if __name__ == "__main__":

    run()
