import argparse
import json

from analytics import (
    contratos_por_periodo,
    fornecedores_mais_recorrentes,
    maiores_contratos,
    orgaos_que_mais_contratam,
    resumo_analitico,
)
from database import criar_tabela


def main(argv=None):
    parser = argparse.ArgumentParser(description="Consultas analiticas da base contratual.")
    parser.add_argument(
        "consulta",
        choices=[
            "fornecedores",
            "orgaos",
            "maiores-contratos",
            "periodo",
            "resumo",
        ],
        help="Consulta analitica a executar.",
    )
    parser.add_argument("--limite", type=int, default=10, help="Quantidade maxima de registros.")
    parser.add_argument("--ano", type=int, help="Filtra contratos por ano de processamento.")
    parser.add_argument("--mes", type=int, help="Filtra contratos por mes de processamento.")
    parser.add_argument("--data-inicio", help="Filtra a partir da data YYYY-MM-DD.")
    parser.add_argument("--data-fim", help="Filtra ate a data YYYY-MM-DD.")
    parser.add_argument("--json", action="store_true", help="Imprime resultado em JSON.")

    args = parser.parse_args(argv)

    criar_tabela()

    if args.consulta == "fornecedores":
        resultado = fornecedores_mais_recorrentes(limite=args.limite)
    elif args.consulta == "orgaos":
        resultado = orgaos_que_mais_contratam(limite=args.limite)
    elif args.consulta == "maiores-contratos":
        resultado = maiores_contratos(limite=args.limite)
    elif args.consulta == "periodo":
        resultado = contratos_por_periodo(
            ano=args.ano,
            mes=args.mes,
            data_inicio=args.data_inicio,
            data_fim=args.data_fim,
        )
    else:
        resultado = resumo_analitico()

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0

    _imprimir_resultado(resultado)
    return 0


def _imprimir_resultado(resultado):
    if isinstance(resultado, dict):
        for titulo, registros in resultado.items():
            print(f"\n{titulo}")
            print("=" * len(titulo))
            _imprimir_tabela(registros)

        return

    _imprimir_tabela(resultado)


def _imprimir_tabela(registros):
    if not registros:
        print("Nenhum registro encontrado.")
        return

    colunas = list(registros[0].keys())
    larguras = {
        coluna: max(len(coluna), *(len(_formatar(registro[coluna])) for registro in registros))
        for coluna in colunas
    }

    print(" | ".join(coluna.ljust(larguras[coluna]) for coluna in colunas))
    print("-+-".join("-" * larguras[coluna] for coluna in colunas))

    for registro in registros:
        print(" | ".join(_formatar(registro[coluna]).ljust(larguras[coluna]) for coluna in colunas))


def _formatar(valor):
    if isinstance(valor, list):
        return "; ".join(str(item) for item in valor)

    if valor is None:
        return ""

    return str(valor)


if __name__ == "__main__":
    raise SystemExit(main())
