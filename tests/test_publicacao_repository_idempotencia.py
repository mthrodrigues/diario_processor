from unittest import TestCase

from infra.db.repositories.publicacao_repository import PublicacaoRepository


class CursorUpsert:
    def __init__(self, conn):
        self.conn = conn
        self.resultado = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append((sql, params))
        chave = (params[20], params[1])
        registro = self.conn.publicacoes.get(chave)

        if registro is None:
            registro = {"id": self.conn.proximo_id, "params": params}
            self.conn.proximo_id += 1
            self.conn.publicacoes[chave] = registro
        else:
            anteriores = registro["params"]
            registro["params"] = tuple(
                novo if novo is not None else anterior
                for novo, anterior in zip(params, anteriores)
            )

        self.resultado = (registro["id"],)

    def fetchone(self):
        return self.resultado


class ConexaoUpsert:
    def __init__(self):
        self.executed = []
        self.publicacoes = {}
        self.proximo_id = 1

    def cursor(self):
        return CursorUpsert(self)


def publicacao(**alteracoes):
    dados = {
        "diario_id": 3279,
        "numero_bloco": 7,
        "arquivo_path": "C:/pdfs/diario_3279.pdf",
        "texto_bloco": "Texto bruto original.",
        "tipo": "contrato",
        "processo": "1/2026",
        "contrato": "001/2026",
        "contratante": "Municipio",
        "fornecedor": "Fornecedor original",
        "cnpj": "00.000.000/0001-00",
        "valores": [100.0],
        "valor_principal": 100.0,
        "vigencia": "12 meses",
        "objeto": "Objeto original",
        "fornecedor_normalizado": "FORNECEDOR ORIGINAL",
        "contratante_normalizado": "MUNICIPIO",
        "processo_normalizado": "1/2026",
        "data_publicacao": "2026-01-01",
        "contrato_normalizado": "001/2026",
        "pdf_hash": "a" * 64,
        "parser_version": "parser-v1",
    }
    dados.update(alteracoes)
    return dados


class PublicacaoRepositoryIdempotenciaTest(TestCase):
    def setUp(self):
        self.conn = ConexaoUpsert()
        self.repository = PublicacaoRepository(self.conn, schema="diario")

    def test_primeira_gravacao_cria_id_e_segunda_com_mesma_chave_retorna_o_mesmo(self):
        primeiro_id = self.repository.salvar_publicacao(**publicacao())
        segundo_id = self.repository.salvar_publicacao(**publicacao())

        self.assertEqual(primeiro_id, segundo_id)
        self.assertEqual(len(self.conn.publicacoes), 1)

    def test_conflito_atualiza_campos_extraidos_sem_criar_nova_publicacao(self):
        primeiro_id = self.repository.salvar_publicacao(**publicacao())
        segundo_id = self.repository.salvar_publicacao(
            **publicacao(fornecedor="Fornecedor revisado", parser_version="parser-v2")
        )

        registro = next(iter(self.conn.publicacoes.values()))
        self.assertEqual(primeiro_id, segundo_id)
        self.assertEqual(registro["params"][9], "Fornecedor revisado")
        self.assertEqual(registro["params"][-1], "parser-v2")

    def test_conflito_preserva_valores_existentes_quando_nova_extracao_traz_null(self):
        self.repository.salvar_publicacao(**publicacao())
        self.repository.salvar_publicacao(
            **publicacao(
                texto_bloco=None,
                fornecedor=None,
                valor_principal=None,
                objeto=None,
                parser_version=None,
            )
        )

        registro = next(iter(self.conn.publicacoes.values()))
        self.assertEqual(registro["params"][3], "Texto bruto original.")
        self.assertEqual(registro["params"][9], "Fornecedor original")
        self.assertEqual(registro["params"][14], 100.0)
        self.assertEqual(registro["params"][16], "Objeto original")
        self.assertEqual(registro["params"][-1], "parser-v1")

    def test_blocos_e_pdfs_diferentes_criam_ids_diferentes(self):
        primeiro_id = self.repository.salvar_publicacao(**publicacao())
        bloco_diferente_id = self.repository.salvar_publicacao(**publicacao(numero_bloco=8))
        pdf_diferente_id = self.repository.salvar_publicacao(**publicacao(pdf_hash="b" * 64))

        self.assertEqual(len({primeiro_id, bloco_diferente_id, pdf_diferente_id}), 3)
        self.assertEqual(len(self.conn.publicacoes), 3)

    def test_upsert_nao_depende_de_ja_processado(self):
        primeiro_id = self.repository.salvar_publicacao(**publicacao())
        segundo_id = self.repository.salvar_publicacao(**publicacao())

        self.assertEqual(primeiro_id, segundo_id)
        self.assertFalse(any("SELECT 1" in sql for sql, _ in self.conn.executed))