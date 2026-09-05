import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import BASE_DIARIO_PATH, get_postgres_config
from infra.db.connection import postgres_connection
from infra.db.migrations.runner import quote_ident
from scanner import calcular_pdf_hash, extrair_diario_id


def listar_pdfs_com_hash(base_path):
    encontrados = []
    invalidos = []

    for pdf_path in sorted(Path(base_path).rglob("*.pdf")):
        try:
            diario_id = extrair_diario_id(pdf_path)
            pdf_hash = calcular_pdf_hash(pdf_path)
        except (OSError, ValueError) as exc:
            invalidos.append(
                {
                    "arquivo_path": str(pdf_path),
                    "erro": str(exc),
                }
            )
            continue

        encontrados.append(
            {
                "arquivo_path": str(pdf_path),
                "diario_id": diario_id,
                "pdf_hash": pdf_hash,
            }
        )

    return encontrados, invalidos


def listar_publicacoes(conn, schema):
    schema_sql = quote_ident(schema)

    with conn.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute(
            f"""
            SELECT id, arquivo_path, diario_id, numero_bloco, pdf_hash
            FROM {schema_sql}.publicacoes
            ORDER BY id
            """
        )
        return [
            {
                "id": linha[0],
                "arquivo_path": linha[1],
                "diario_id": linha[2],
                "numero_bloco": linha[3],
                "pdf_hash": linha[4],
            }
            for linha in cursor.fetchall()
        ]


def gerar_relatorio(pdfs, publicacoes, erros_pdf=None):
    pdfs_por_path = {
        pdf["arquivo_path"]: pdf
        for pdf in pdfs
    }
    publicacoes_ordenadas = sorted(publicacoes, key=lambda publicacao: publicacao["id"])
    candidatos_por_chave = defaultdict(list)
    sem_hash = []
    arquivos_ausentes = []
    diario_id_inconsistente = []
    hash_inconsistente = []

    for publicacao in publicacoes_ordenadas:
        pdf = pdfs_por_path.get(publicacao["arquivo_path"])

        if not publicacao["pdf_hash"]:
            sem_hash.append(publicacao["id"])

        if pdf is None:
            arquivos_ausentes.append(
                {
                    "id": publicacao["id"],
                    "arquivo_path": publicacao["arquivo_path"],
                    "diario_id": publicacao["diario_id"],
                }
            )
            continue

        if publicacao["diario_id"] != pdf["diario_id"]:
            diario_id_inconsistente.append(
                {
                    "id": publicacao["id"],
                    "arquivo_path": publicacao["arquivo_path"],
                    "diario_id_banco": publicacao["diario_id"],
                    "diario_id_arquivo": pdf["diario_id"],
                }
            )

        if publicacao["pdf_hash"] and publicacao["pdf_hash"] != pdf["pdf_hash"]:
            hash_inconsistente.append(
                {
                    "id": publicacao["id"],
                    "arquivo_path": publicacao["arquivo_path"],
                    "pdf_hash_banco": publicacao["pdf_hash"],
                    "pdf_hash_arquivo": pdf["pdf_hash"],
                }
            )

        candidatos_por_chave[(pdf["pdf_hash"], publicacao["numero_bloco"])].append(
            publicacao["id"]
        )

    conflitos = [
        {
            "pdf_hash": pdf_hash,
            "numero_bloco": numero_bloco,
            "publicacao_ids": sorted(ids),
        }
        for (pdf_hash, numero_bloco), ids in sorted(candidatos_por_chave.items())
        if len(ids) > 1
    ]

    return {
        "arquivos_pdf_disponiveis": len(pdfs),
        "pdfs_escaneados": sorted(
            pdfs,
            key=lambda pdf: pdf["arquivo_path"],
        ),
        "publicacoes_analisadas": len(publicacoes_ordenadas),
        "publicacoes_sem_hash_atual": sem_hash,
        "arquivos_do_banco_ausentes_no_filesystem": arquivos_ausentes,
        "diario_id_inconsistente": diario_id_inconsistente,
        "hash_inconsistente": hash_inconsistente,
        "conflitos_candidatos_pdf_hash_numero_bloco": conflitos,
        "quantidade_conflitos_candidatos": len(conflitos),
        "pdfs_invalidos": sorted(erros_pdf or [], key=lambda erro: erro["arquivo_path"]),
    }


def executar_auditoria(base_path, schema):
    pdfs, erros_pdf = listar_pdfs_com_hash(base_path)

    with postgres_connection() as conn:
        publicacoes = listar_publicacoes(conn, schema)

    return gerar_relatorio(pdfs, publicacoes, erros_pdf)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audita candidatos a conflitos por (pdf_hash, numero_bloco) sem alterar dados."
    )
    parser.add_argument("--base-dir", type=Path, default=BASE_DIARIO_PATH)
    parser.add_argument("--schema", default=get_postgres_config().schema)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    relatorio = executar_auditoria(args.base_dir, args.schema)
    conteudo = json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True)

    if args.output:
        args.output.write_text(conteudo + "\n", encoding="utf-8")
    else:
        print(conteudo)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())