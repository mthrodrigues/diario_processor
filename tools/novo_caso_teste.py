#!/usr/bin/env python3
"""
Cria um novo caso de teste do corpus.

Uso:

    py tools/novo_caso_teste.py q003_memorando

Resultado:

tests/
└── corpus/
    ├── textos/
    │   └── q003_memorando.txt
    └── expected/
        └── q003_memorando.json
"""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent

TEXTOS = ROOT / "tests" / "corpus" / "textos"
EXPECTED = ROOT / "tests" / "corpus" / "expected"


JSON_TEMPLATE = {
    "blocos": []
}


def criar_arquivo(caminho: Path, conteudo: str = ""):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    if caminho.exists():
        print(f"[SKIP] {caminho.relative_to(ROOT)} já existe.")
        return

    caminho.write_text(conteudo, encoding="utf-8")
    print(f"[OK]   {caminho.relative_to(ROOT)} criado.")


def criar_json(caminho: Path):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    if caminho.exists():
        print(f"[SKIP] {caminho.relative_to(ROOT)} já existe.")
        return

    caminho.write_text(
        json.dumps(
            JSON_TEMPLATE,
            ensure_ascii=False,
            indent=4
        ),
        encoding="utf-8"
    )

    print(f"[OK]   {caminho.relative_to(ROOT)} criado.")


def main():

    if len(sys.argv) != 2:
        print("Uso:")
        print("    py tools/novo_caso_teste.py nome_do_caso")
        sys.exit(1)

    nome = sys.argv[1].strip()

    criar_arquivo(TEXTOS / f"{nome}.txt")
    criar_json(EXPECTED / f"{nome}.json")

    print()
    print("Caso criado com sucesso.")
    print()
    print(f"Texto   : tests/corpus/textos/{nome}.txt")
    print(f"Esperado: tests/corpus/expected/{nome}.json")


if __name__ == "__main__":
    main()