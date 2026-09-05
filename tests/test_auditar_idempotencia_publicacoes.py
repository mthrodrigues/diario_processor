import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

from tools.auditar_idempotencia_publicacoes import (
    gerar_relatorio,
    listar_pdfs_com_hash,
    listar_publicacoes,
)


class CursorSomenteLeitura:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append((sql, params))

    def fetchall(self):
        return self.conn.linhas


class ConexaoSomenteLeitura:
    def __init__(self, linhas):
        self.linhas = linhas
        self.executed = []

    def cursor(self):
        return CursorSomenteLeitura(self)


class AuditarIdempotenciaPublicacoesTest(TestCase):
    def test_script_executado_da_raiz_importa_modulos_do_projeto(self):
        raiz_projeto = Path(__file__).resolve().parent.parent

        resultado = subprocess.run(
            [
                sys.executable,
                "tools/auditar_idempotencia_publicacoes.py",
                "--help",
            ],
            cwd=raiz_projeto,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertNotIn("ModuleNotFoundError", resultado.stderr)
        self.assertIn("Audita candidatos", resultado.stdout)

    def test_listar_pdfs_com_hash_calcula_hash_e_reporta_nome_invalido(self):
        with tempfile.TemporaryDirectory() as diretorio:
            base_path = Path(diretorio)
            (base_path / "diario_3279.pdf").write_bytes(b"pdf valido")
            (base_path / "sem_identificador.pdf").write_bytes(b"pdf invalido")

            pdfs, erros = listar_pdfs_com_hash(base_path)

        self.assertEqual(len(pdfs), 1)
        self.assertEqual(pdfs[0]["diario_id"], 3279)
        self.assertEqual(
            pdfs[0]["pdf_hash"],
            hashlib.sha256(b"pdf valido").hexdigest(),
        )
        self.assertEqual(len(erros), 1)
        self.assertIn("sem_identificador.pdf", erros[0]["arquivo_path"])

    def test_listar_publicacoes_emite_apenas_comandos_de_leitura(self):
        conn = ConexaoSomenteLeitura(
            [(1, "C:/pdfs/diario_3279.pdf", 3279, 1, None)]
        )

        publicacoes = listar_publicacoes(conn, "diario")

        self.assertEqual(publicacoes[0]["id"], 1)
        comandos = [sql.strip().upper() for sql, _ in conn.executed]
        self.assertEqual(comandos[0], "SET TRANSACTION READ ONLY")
        self.assertTrue(comandos[1].startswith("SELECT"))
        self.assertFalse(any("INSERT" in comando for comando in comandos))
        self.assertFalse(any("UPDATE" in comando for comando in comandos))
        self.assertFalse(any("DELETE" in comando for comando in comandos))

    def test_gerar_relatorio_identifica_conflitos_e_inconsistencias(self):
        pdf_hash = "a" * 64
        relatorio = gerar_relatorio(
            pdfs=[
                {
                    "arquivo_path": "C:/pdfs/diario_3279.pdf",
                    "diario_id": 3279,
                    "pdf_hash": pdf_hash,
                }
            ],
            publicacoes=[
                {
                    "id": 3,
                    "arquivo_path": "C:/pdfs/diario_3279.pdf",
                    "diario_id": 3279,
                    "numero_bloco": 7,
                    "pdf_hash": None,
                },
                {
                    "id": 1,
                    "arquivo_path": "C:/pdfs/diario_3279.pdf",
                    "diario_id": 3279,
                    "numero_bloco": 7,
                    "pdf_hash": "b" * 64,
                },
                {
                    "id": 2,
                    "arquivo_path": "C:/pdfs/ausente.pdf",
                    "diario_id": 3278,
                    "numero_bloco": 1,
                    "pdf_hash": None,
                },
            ],
        )

        self.assertEqual(relatorio["publicacoes_sem_hash_atual"], [2, 3])
        self.assertEqual(
            relatorio["pdfs_escaneados"],
            [
                {
                    "arquivo_path": "C:/pdfs/diario_3279.pdf",
                    "diario_id": 3279,
                    "pdf_hash": pdf_hash,
                }
            ],
        )
        self.assertEqual(relatorio["quantidade_conflitos_candidatos"], 1)
        self.assertEqual(
            relatorio["conflitos_candidatos_pdf_hash_numero_bloco"],
            [{"pdf_hash": pdf_hash, "numero_bloco": 7, "publicacao_ids": [1, 3]}],
        )
        self.assertEqual(
            relatorio["arquivos_do_banco_ausentes_no_filesystem"],
            [{"id": 2, "arquivo_path": "C:/pdfs/ausente.pdf", "diario_id": 3278}],
        )
        self.assertEqual(relatorio["hash_inconsistente"][0]["id"], 1)