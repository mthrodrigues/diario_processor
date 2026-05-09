from scanner import listar_pdfs, extrair_diario_id
from extractor import extrair_texto
from parser import segmentar_publicacoes
from processor import extrair_metadados_bloco

from database import (
    criar_tabela,
    salvar_publicacao,
    ja_processado
)


def run():
    print("Iniciando Diário Processor...\n")

    # 🗄️ Garante que a tabela existe
    criar_tabela()

    # 🔍 Busca PDFs
    pdfs = listar_pdfs()

    print(f"Total de PDFs encontrados: {len(pdfs)}\n")

    novos = 0
    ignorados = 0

    for pdf in pdfs:

        try:

            # ⏭️ Pula PDFs já processados
            if ja_processado(pdf):
                ignorados += 1
                continue

            diario_id = extrair_diario_id(pdf)

            print(f"\n================================================")
            print(f"Processando diário {diario_id}")
            print(f"Arquivo: {pdf}")
            print(f"================================================")

            # 📄 Extrai texto completo
            texto = extrair_texto(pdf)

            # ✂️ Segmenta em publicações
            blocos = segmentar_publicacoes(texto)

            print(f"\nBlocos encontrados: {len(blocos)}")

            # 🔍 Processa bloco a bloco
            for i, bloco in enumerate(blocos, start=1):

                print(f"\n--- BLOCO {i} ---")

                metadados = extrair_metadados_bloco(bloco)

                print(f"Tipo identificado: {metadados['tipo']}")
                print(f"Relevância documental: {metadados['relevancia']}")
                print(f"Prioritário para inteligência contratual: {metadados['prioritario']}")
                print(f"Processo identificado: {metadados['processo']}")
                print(f"Contrato identificado: {metadados['contrato']}")
                print(f"Fornecedor identificado: {metadados['fornecedor']}")
                print(f"Fornecedor normalizado: {metadados['fornecedor_normalizado']}")
                print(f"Contratante identificado: {metadados['contratante']}")
                print(f"Contratante normalizado: {metadados['contratante_normalizado']}")
                print(f"Vigência identificada: {metadados['vigencia']}")
                print(f"Objeto identificado: {metadados['objeto']}")
                print(f"CNPJ identificado: {metadados['cnpj']}")

                if metadados["valores"]:
                    print(f"Valores encontrados: {metadados['valores'][:5]}")
                else:
                    print("Nenhum valor encontrado.")

                print(f"Valor principal identificado: {metadados['valor_principal']}")

                # 💾 Salva CADA BLOCO
                salvar_publicacao(
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
