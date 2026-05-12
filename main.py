from scanner import (
    listar_pdfs,
    extrair_diario_id,
    extrair_data_publicacao
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

from events import extrair_eventos_bloco

from infra.db.repositories.entity_relationship_repository import (
    EntityRelationshipRepository
)

from taxonomy.relation_resolver import (
    resolver_relacao_evento
)

from infra.db.repositories.timeline_repository import (
    TimelineRepository
)

def run():

    print("Iniciando Diário Processor...\n")

    with postgres_connection() as conn:

        repository = PublicacaoRepository(conn)

        evento_repository = EventoRepository(conn)

        entity_repository = EntityRepository(conn)
        relationship_repository = (
            EntityRelationshipRepository(conn)
        )
        timeline_repository = TimelineRepository(conn)

        # =====================================================
        # PDFs
        # =====================================================

        pdfs = listar_pdfs()

        print(f"Total de PDFs encontrados: {len(pdfs)}\n")

        novos = 0
        ignorados = 0

        # =====================================================
        # LOOP PDFs
        # =====================================================

        for pdf in pdfs:

            try:

                # =============================================
                # INCREMENTALIDADE
                # =============================================

                if repository.ja_processado(pdf):

                    ignorados += 1

                    continue

                diario_id = extrair_diario_id(pdf)

                print("\n================================================")
                print(f"Processando diário {diario_id}")
                print(f"Arquivo: {pdf}")
                print("================================================")

                # =============================================
                # TEXTO
                # =============================================

                texto = extrair_texto(pdf)

                # =============================================
                # DATA CONTEXTUAL DO DIÁRIO
                # =============================================

                data_publicacao = extrair_data_publicacao(texto)

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

                for i, bloco in enumerate(blocos, start=1):

                    print(f"\n--- BLOCO {i} ---")

                    metadados = extrair_metadados_bloco(bloco)

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

                        # =====================================
                        # SALVA EVENTO
                        # =====================================

                        evento_id = (
                            evento_repository.salvar_evento(
                                evento,
                                data_publicacao=data_publicacao
                            )
                        )

                        print("EVENTO SALVO:", evento_id)

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
                                    "pessoa",
                                    agente_nome
                                )
                            )

                            evento_repository.relacionar_entidade(
                                evento_id,
                                entidade_pessoa_id,
                                "agente"
                            )

                            # =========================================
                            # RELAÇÃO PESSOA → ÓRGÃO
                            # =========================================

                            orgao_nome = evento.get("orgao")

                            if orgao_nome:

                                entidade_orgao_id = (
                                    entity_repository.obter_ou_criar(
                                        "orgao",
                                        orgao_nome
                                    )
                                )

                                tipo_relacao = resolver_relacao_evento(
                                    evento.get("tipo_evento")
                                )

                                relationship_repository.criar_relacao(

                                    entidade_pessoa_id,
                                    entidade_orgao_id,

                                    tipo_relacao,

                                    diario_id=diario_id,
                                    data_publicacao=data_publicacao
                                )

                                # =========================================
                                # TIMELINE
                                # =========================================

                                if tipo_relacao == "NOMEADO_EM":

                                    timeline_repository.abrir_vinculo(

                                        entidade_pessoa_id,
                                        entidade_orgao_id,

                                        "LOTACAO",

                                        data_publicacao,

                                        evento_id
                                    )

                                elif tipo_relacao == "EXONERADO_DE":

                                    timeline_repository.fechar_vinculo(

                                        entidade_pessoa_id,
                                        entidade_orgao_id,

                                        data_publicacao,

                                        evento_id
                                    )

                            evento_repository.relacionar_entidade(
                                evento_id,
                                entidade_id,
                                "agente"
                            )

                        # =====================================
                        # ÓRGÃO
                        # =====================================

                        orgao_nome = evento.get("orgao")

                        if orgao_nome:

                            entidade_id = (
                                entity_repository.obter_ou_criar(
                                    "orgao",
                                    orgao_nome
                                )
                            )

                            evento_repository.relacionar_entidade(
                                evento_id,
                                entidade_id,
                                "orgao"
                            )

                        # =====================================
                        # EMPRESA
                        # =====================================

                        empresa_nome = (
                            evento.get("entidade_destino", {})
                            .get("nome")
                        )

                        if empresa_nome:

                            entidade_id = (
                                entity_repository.obter_ou_criar(
                                    "empresa",
                                    empresa_nome
                                )
                            )

                            evento_repository.relacionar_entidade(
                                evento_id,
                                entidade_id,
                                "contratado"
                            )

                    # =========================================
                    # DEBUG METADADOS
                    # =========================================

                    print(f"Tipo identificado: {metadados['tipo']}")

                    print(
                        f"Relevância documental: "
                        f"{metadados['relevancia']}"
                    )

                    print(
                        f"Prioritário para inteligência contratual: "
                        f"{metadados['prioritario']}"
                    )

                    print(
                        f"Processo identificado: "
                        f"{metadados['processo']}"
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

                        print("Nenhum valor encontrado.")

                    print(
                        f"Valor principal identificado: "
                        f"{metadados['valor_principal']}"
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
                        metadados["relevancia"],
                        metadados["prioritario"],
                        metadados["vigencia"],
                        metadados["objeto"],
                        metadados["fornecedor_normalizado"],
                        metadados["contratante_normalizado"]
                    )

                novos += 1

            except Exception as e:

                print(f"Erro ao processar {pdf}: {e}")

        print("\n========================================")
        print("Resumo da execução:")
        print(f"Novos processados: {novos}")
        print(f"Ignorados (já existentes): {ignorados}")
        print("========================================")


if __name__ == "__main__":

    run()