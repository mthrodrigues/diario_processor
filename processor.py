import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from classifier import deve_enriquecer_contratual
from config import get_postgres_config
from normalizer import (
    normalize_contratante,
    normalize_contrato,
    normalize_fornecedor,
    normalize_processo,
)
from parser import (
    extrair_cnpj,
    extrair_contratante,
    extrair_contrato,
    extrair_fornecedor,
    extrair_objeto,
    extrair_processo,
    extrair_valor_principal,
    extrair_valores,
    extrair_vigencia,
    identificar_tipo,
)


def _emitir_debug_etapa1(metadados):
    cfg = get_postgres_config()
    try:
        repo_root = Path(__file__).resolve().parent
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
        branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception as exc:
        commit_sha = f"ERR:{exc}"
        branch_name = f"ERR:{exc}"

    print("[AUDIT][ETAPA1]", {
        "commit_sha": commit_sha,
        "branch": branch_name,
        "pid": os.getpid(),
        "db": cfg.db,
        "host": cfg.host,
        "schema": cfg.schema,
    })
    print("[AUDIT][ETAPA1][metadados]", {
        "contratante": metadados.get("contratante"),
        "contratante_normalizado": metadados.get("contratante_normalizado"),
    })


def extrair_metadados_bloco(texto_bloco):
    tipo = identificar_tipo(texto_bloco)
    metadados = {
        "tipo": tipo,
        "processo": extrair_processo(texto_bloco),
        "processo_normalizado": None,
        "contrato": extrair_contrato(texto_bloco),
        "contrato_normalizado": None,
        "cnpj": extrair_cnpj(texto_bloco),
        "valores": extrair_valores(texto_bloco),
        "contratante": None,
        "contratante_normalizado": None,
        "fornecedor": None,
        "fornecedor_normalizado": None,
        "valor_principal": None,
        "vigencia": None,
        "objeto": None,
    }

    metadados["processo_normalizado"] = normalize_processo(metadados["processo"])
    metadados["contrato_normalizado"] = normalize_contrato(metadados["contrato"])

    if deve_enriquecer_contratual(tipo):
        contratante = extrair_contratante(texto_bloco)
        fornecedor = extrair_fornecedor(texto_bloco)

        metadados.update(
            {
                "contratante": contratante,
                "contratante_normalizado": normalize_contratante(contratante),
                "fornecedor": fornecedor,
                "fornecedor_normalizado": normalize_fornecedor(fornecedor),
                "valor_principal": extrair_valor_principal(texto_bloco),
                "vigencia": extrair_vigencia(texto_bloco),
                "objeto": extrair_objeto(texto_bloco),
            }
        )

    _emitir_debug_etapa1(metadados)

    return metadados
