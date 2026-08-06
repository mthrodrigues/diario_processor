import argparse
import time
from collections import Counter
from dataclasses import dataclass, field

from database import conectar, criar_tabela
from normalizer import (
    normalize_contratante,
    normalize_contrato,
    normalize_fornecedor,
    normalize_processo,
)
from processor import extrair_metadados_bloco


CAMPOS_ANALITICOS = [
    "tipo",
    "processo",
    "contrato",
    "cnpj",
    "valores",
    "valor_principal",
    "vigencia",
    "objeto",
    "fornecedor",
    "contratante",
]

CAMPOS_NORMALIZACAO = [
    "fornecedor_normalizado",
    "contratante_normalizado",
    "processo_normalizado",
    "contrato_normalizado",
]

CAMPOS_BACKFILL = CAMPOS_ANALITICOS + CAMPOS_NORMALIZACAO


@dataclass
class BackfillResumo:
    analisados: int = 0
    atualizados: int = 0
    campos_preenchidos: Counter = field(default_factory=Counter)
    tempo_total: float = 0.0

    def registrar_update(self, campos):
        if not campos:
            return

        self.atualizados += 1
        self.campos_preenchidos.update(campos)

    def as_dict(self):
        return {
            "analisados": self.analisados,
            "atualizados": self.atualizados,
            "campos_preenchidos": dict(self.campos_preenchidos),
            "tempo_total": self.tempo_total,
        }


def executar_backfill(limit=None, only_normalization=False, only_analytics_fields=False, conn=None):
    if only_normalization and only_analytics_fields:
        raise ValueError("Use apenas um modo: only_normalization ou only_analytics_fields.")

    inicio = time.perf_counter()
    fechar_conn = False

    if conn is None:
        criar_tabela()
        conn = conectar()
        fechar_conn = True

    resumo = BackfillResumo()

    try:
        campos_alvo = _campos_alvo(only_normalization, only_analytics_fields)
        registros = _buscar_registros(conn, limit, campos_alvo)
        resumo.analisados = len(registros)

        for registro in registros:
            atualizacoes = preparar_atualizacoes(
                registro,
                only_normalization=only_normalization,
                only_analytics_fields=only_analytics_fields,
            )

            if not atualizacoes:
                continue

            _atualizar_registro(conn, registro["id"], atualizacoes)
            resumo.registrar_update(atualizacoes.keys())

        conn.commit()
    finally:
        resumo.tempo_total = time.perf_counter() - inicio

        if fechar_conn:
            conn.close()

    return resumo


def _campos_alvo(only_normalization=False, only_analytics_fields=False):
    if only_normalization:
        return CAMPOS_NORMALIZACAO

    if only_analytics_fields:
        return CAMPOS_ANALITICOS

    return CAMPOS_BACKFILL


def preparar_atualizacoes(registro, only_normalization=False, only_analytics_fields=False):
    texto_bloco = registro.get("texto_bloco") or ""
    metadados = extrair_metadados_bloco(texto_bloco) if texto_bloco else {}
    atualizacoes = {}

    if not only_normalization:
        _preparar_campos_analiticos(registro, metadados, atualizacoes)

    if not only_analytics_fields:
        _preparar_campos_normalizados(registro, metadados, atualizacoes)

    return atualizacoes


def _preparar_campos_analiticos(registro, metadados, atualizacoes):
    for campo in CAMPOS_ANALITICOS:
        if not _campo_vazio(registro.get(campo)):
            continue

        valor = metadados.get(campo)

        if _campo_vazio(valor):
            continue

        atualizacoes[campo] = _normalizar_valor_para_sql(valor)


def _preparar_campos_normalizados(registro, metadados, atualizacoes):
    if _campo_vazio(registro.get("fornecedor_normalizado")):
        fornecedor_raw = _primeiro_valor(
            registro.get("fornecedor"),
            atualizacoes.get("fornecedor"),
            metadados.get("fornecedor"),
        )
        fornecedor_normalizado = normalize_fornecedor(fornecedor_raw)

        if not _campo_vazio(fornecedor_normalizado):
            atualizacoes["fornecedor_normalizado"] = fornecedor_normalizado

    if _campo_vazio(registro.get("contratante_normalizado")):
        contratante_raw = _primeiro_valor(
            registro.get("contratante"),
            atualizacoes.get("contratante"),
            metadados.get("contratante"),
        )
        contratante_normalizado = normalize_contratante(contratante_raw)

        if not _campo_vazio(contratante_normalizado):
            atualizacoes["contratante_normalizado"] = contratante_normalizado

    if _campo_vazio(registro.get("processo_normalizado")):
        processo_raw = _primeiro_valor(
            registro.get("processo"),
            atualizacoes.get("processo"),
            metadados.get("processo"),
        )
        processo_normalizado = normalize_processo(processo_raw)

        if not _campo_vazio(processo_normalizado):
            atualizacoes["processo_normalizado"] = processo_normalizado

    if _campo_vazio(registro.get("contrato_normalizado")):
        contrato_raw = _primeiro_valor(
            registro.get("contrato"),
            atualizacoes.get("contrato"),
            metadados.get("contrato"),
        )
        contrato_normalizado = normalize_contrato(contrato_raw)

        if not _campo_vazio(contrato_normalizado):
            atualizacoes["contrato_normalizado"] = contrato_normalizado


def _buscar_registros(conn, limit=None, campos_alvo=None):
    campos_alvo = campos_alvo or CAMPOS_BACKFILL
    campos = ["id", "texto_bloco"] + CAMPOS_BACKFILL
    sql = f"""
    SELECT {", ".join(campos)}
    FROM publicacoes
    WHERE {_where_incompletos(campos_alvo)}
    ORDER BY id ASC
    """
    parametros = []

    if limit is not None:
        sql += " LIMIT ?"
        parametros.append(limit)

    cursor = conn.cursor()
    cursor.execute(sql, parametros)
    colunas = [descricao[0] for descricao in cursor.description]

    return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]


def _where_incompletos(campos_alvo):
    condicoes = []

    for campo in campos_alvo:
        condicoes.append(f"{campo} IS NULL")
        condicoes.append(f"TRIM(CAST({campo} AS TEXT)) = ''")

    return " OR ".join(condicoes)


def _atualizar_registro(conn, registro_id, atualizacoes):
    atribuicoes = ", ".join(f"{campo} = ?" for campo in atualizacoes)
    valores = list(atualizacoes.values()) + [registro_id]
    conn.execute(
        f"""
        UPDATE publicacoes
        SET {atribuicoes}
        WHERE id = ?
        """,
        valores,
    )


def _campo_vazio(valor):
    if valor is None:
        return True

    if isinstance(valor, str):
        return valor.strip() == ""

    return False


def _normalizar_valor_para_sql(valor):
    if isinstance(valor, bool):
        return 1 if valor else 0

    if isinstance(valor, list):
        import json

        return json.dumps(valor)

    return valor


def _primeiro_valor(*valores):
    for valor in valores:
        if not _campo_vazio(valor):
            return valor

    return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Backfill deterministico de campos derivados em publicacoes antigas."
    )
    parser.add_argument("--limit", type=int, help="Limita a quantidade de registros analisados.")
    parser.add_argument(
        "--only-normalization",
        action="store_true",
        help="Preenche campos normalizados de fornecedor, contratante e processo.",
    )
    parser.add_argument(
        "--only-analytics-fields",
        action="store_true",
        help="Preenche apenas campos analiticos derivados, sem normalizacao.",
    )

    args = parser.parse_args(argv)
    resumo = executar_backfill(
        limit=args.limit,
        only_normalization=args.only_normalization,
        only_analytics_fields=args.only_analytics_fields,
    )

    _imprimir_resumo(resumo)
    return 0


def _imprimir_resumo(resumo):
    print("Backfill concluido")
    print(f"Registros analisados: {resumo.analisados}")
    print(f"Registros atualizados: {resumo.atualizados}")
    print("Campos preenchidos:")

    if resumo.campos_preenchidos:
        for campo, quantidade in sorted(resumo.campos_preenchidos.items()):
            print(f"  {campo}: {quantidade}")
    else:
        print("  nenhum")

    print(f"Tempo total: {resumo.tempo_total:.3f}s")


if __name__ == "__main__":
    raise SystemExit(main())
