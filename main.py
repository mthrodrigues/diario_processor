import sys
import time
import pdfplumber

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from scanner import (
    listar_pdfs,
    calcular_pdf_hash,
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

from extractor import extrair_texto_paginado
from parser import (
    sanear_texto_paginado,
    segmentar_publicacoes_paginado,
    serializar_bloco_paginado,
    serializar_texto_paginado,
)
from processor import extrair_metadados_bloco

from infra.db.connection import postgres_connection

from infra.db.repositories.publicacao_repository import (
    PublicacaoRepository
)

from infra.db.repositories.pot_repository import (
    PotRepository
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

from pot_extractor import (
    extrair_publicacoes_pot_estruturadas,
)
from pot_segmentation import ajustar_blocos_pot_estruturais

from logging_setup import setup_logging, novo_run_id, log_sucesso, log_erro


def _timeline_vinculo_valido(tipo_evento, entidade_pessoa_id, entidade_orgao_id):
    if tipo_evento not in (NOMEACAO, EXONERACAO):
        return False

    return (
        entidade_pessoa_id is not None
        and entidade_orgao_id is not None
    )


def run():

    inicio_total = time.time()

    logger = setup_logging()
    run_id = novo_run_id()

    print("--------------------------------------------------")
    print("Iniciando Diário Processor")

    with postgres_connection() as conn:
        repository = PublicacaoRepository(conn)
        pot_repository = PotRepository(conn)

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

            # contexto seguro para o except, antes de qualquer etapa que possa falhar
            diario_id = None
            i = None
            etapa_atual = "incrementalidade"

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

                etapa_atual = "extrair_diario_id"
                diario_id = extrair_diario_id(pdf)

                etapa_atual = "calcular_pdf_hash"
                pdf_hash = calcular_pdf_hash(pdf)

                inicio_pdf = time.time()

                print(f"[{idx}/{len(pdfs)}] Processando diário {diario_id}")
                print(f"  Arquivo: {pdf.name}")

                # =============================================
                # TEXTO
                # =============================================

                etapa_atual = "extrair_texto"
                texto_paginado = extrair_texto_paginado(pdf)
                texto_paginado = sanear_texto_paginado(
                    texto_paginado
                )
                texto = serializar_texto_paginado(texto_paginado)

                # =============================================
                # DATA CONTEXTUAL
                # =============================================

                etapa_atual = "extrair_data_publicacao"
                data_publicacao = (
                    extrair_data_publicacao(texto)
                )

                # =============================================
                # SEGMENTAÇÃO
                # =============================================

                etapa_atual = "segmentar_publicacoes"
                blocos_paginados = segmentar_publicacoes_paginado(
                    texto_paginado
                )
                publicacoes_pot = []

                with pdfplumber.open(pdf) as pdf_aberto:
                    publicacoes_pot_estruturadas = (
                        extrair_publicacoes_pot_estruturadas(
                            pdf_aberto
                        )
                    )
                    blocos_paginados = ajustar_blocos_pot_estruturais(
                        blocos_paginados,
                        publicacoes_pot_estruturadas,
                    )
                    publicacoes_pot = [
                        publicacao["registros"]
                        for publicacao in publicacoes_pot_estruturadas
                    ]

                blocos = [
                    serializar_bloco_paginado(bloco)
                    for bloco in blocos_paginados
                ]

                print(f"  Blocos: {len(blocos)}")

                # =============================================
                # LOOP BLOCOS
                # =============================================

                total_eventos = 0
                ec_aplicacoes = 0
                ec_criterio = None
                pot_indice = 0

                for i, bloco in enumerate(
                    blocos,
                    start=1
                ):

                    etapa_atual = "extrair_metadados_bloco"
                    metadados = extrair_metadados_bloco(
                        bloco
                    )

                    pot_publicacao = None

                    if metadados["tipo"] == "pot":
                        pot_publicacao = publicacoes_pot[pot_indice]
                        pot_indice += 1

                    # ================================
                    # Enriquecimento Contextual (Regra 001)
                    # ================================
                    # Se aplicável, herda contratante institucional do bloco anterior
                    etapa_atual = "enriquecimento_contextual"
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
                    except Exception as e:
                        # não interrompe o pipeline, mas deixa de ser totalmente silencioso
                        log_erro(
                            logger,
                            run_id,
                            str(e),
                            diario_id=diario_id,
                            arquivo=pdf.name,
                            bloco=i,
                            etapa="enriquecimento_contextual",
                        )

                    # preserve bloco atual como "previous" para próxima iteração
                    previous_bloco = bloco
                    previous_metadados = metadados
                    previous_numero = i

                    # =========================================
                    # SALVA PUBLICAÇÃO
                    # =========================================

                    etapa_atual = "salvar_publicacao"
                    publicacao_id = repository.salvar_publicacao(
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
                        metadados["fornecedor_normalizado"],
                        metadados["contratante_normalizado"],
                        metadados["processo_normalizado"],
                        data_publicacao=data_publicacao,
                        contrato_normalizado=metadados["contrato_normalizado"],
                        pdf_hash=pdf_hash,
                    )

                    # =========================================
                    # EVENTOS
                    # =========================================

                    etapa_atual = "extrair_eventos"
                    eventos = extrair_eventos_bloco(
                        metadados,
                        bloco,
                        diario_id,
                        i
                    )

                    # =========================================
                    # LOOP EVENTOS
                    # =========================================

                    for numero_evento, evento in enumerate(eventos, start=1):

                        total_eventos += 1

                        tipo_evento = evento.get("tipo_evento")

                        # =====================================
                        # SALVA EVENTO
                        # =====================================

                        etapa_atual = "salvar_evento"
                        evento_id = (
                            evento_repository.salvar_evento(
                                evento,
                                publicacao_id=publicacao_id,
                                numero_evento=numero_evento,
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

                        etapa_atual = "publicar_evento_canonico"
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
                            log_erro(
                                logger,
                                run_id,
                                str(e),
                                diario_id=diario_id,
                                arquivo=pdf.name,
                                bloco=i,
                                etapa="publicar_evento_canonico",
                            )

                        # =====================================
                        # AGENTE
                        # =====================================

                        entidade_pessoa_id = None
                        entidade_orgao_id = None

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

                    if metadados["tipo"] == "pot":
                        etapa_atual = "salvar_pot"
                        pot_repository.substituir_registros(
                            publicacao_id,
                            pot_publicacao,
                        )

                if pot_indice != len(publicacoes_pot):
                    raise RuntimeError(
                        "Inconsistência na associação POT: "
                        f"{pot_indice} bloco(s) POT processado(s), "
                        f"mas {len(publicacoes_pot)} publicação(ões) POT "
                        "extraída(s) do PDF."
                    )

                novos += 1

                etapa_atual = "commit"
                conn.commit()

                log_sucesso(logger, run_id, diario_id, pdf.name)

                duracao = time.time() - inicio_pdf
                ec_info = (
                    f"{ec_aplicacoes} aplicação(ões) (critério {ec_criterio})"
                    if ec_aplicacoes
                    else "nenhuma aplicação"
                )
                print(f"  Eventos: {total_eventos}")
                print(f"  EC: {ec_info}")
                print(f"  Concluído em: {duracao:.1f}s\n")

            except BaseException as e:

                conn.rollback()

                erros += 1

                import traceback

                print(
                    f"  [ERRO] diário {diario_id} | bloco {i if i is not None else '?'}: {e}"
                )

                traceback.print_exc()

                log_erro(
                    logger,
                    run_id,
                    str(e),
                    diario_id=diario_id,
                    arquivo=pdf.name,
                    bloco=i,
                    etapa=etapa_atual,
                )

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
        except Exception as e:
            conn.rollback()
            log_erro(
                logger,
                run_id,
                str(e),
                etapa="consolidacao_processos",
            )
            raise

        try:
            consolidar_contratos_postgres(
                conn,
                schema=get_postgres_config().schema,
            )
            conn.commit()
            print("Consolidação de contratos concluída.")
        except Exception as e:
            conn.rollback()
            log_erro(
                logger,
                run_id,
                str(e),
                etapa="consolidacao_contratos",
            )
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
