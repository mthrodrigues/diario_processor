from unittest import TestCase

from infra.db.repositories.entity_relationship_repository import (
    EntityRelationshipRepository,
)
from infra.db.repositories.evento_repository import EventoRepository

from unittest.mock import MagicMock

EVENTO = {
    "tipo_evento": "NOMEACAO",
    "agente": {"nome": "Maria da Silva"},
    "cargo": "Diretora",
    "orgao": "Secretaria de Educacao",
    "entidade_origem": {"nome": None},
    "entidade_destino": {"nome": None},
    "processo": None,
    "contrato": None,
    "valor": None,
    "evidencia": {
        "diario_id": 3279,
        "numero_bloco": 7,
        "texto": "Nomear Maria da Silva.",
    },
}


class CursorEventos:
    def __init__(self, conn):
        self.conn = conn
        self.resultado = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.conn.executed.append((sql, params))

        if 'INSERT INTO diario.eventos' not in sql:
            return

        chave = (params[13], params[14])

        existente = self.conn.eventos.get(chave)
        if existente is None:
            existente = {"id": self.conn.proximo_evento_id, "params": params}
            self.conn.proximo_evento_id += 1
            self.conn.eventos[chave] = existente
        else:
            existente["params"] = tuple(
                novo if novo is not None else anterior
                for novo, anterior in zip(params, existente["params"])
            )
        self.resultado = (existente["id"],)

    def fetchone(self):
        return self.resultado


class ConexaoEventos:
    def __init__(self):
        self.executed = []
        self.eventos = {}
        self.proximo_evento_id = 1

    def cursor(self):
        return CursorEventos(self)


class EventoRepositoryIdempotenciaTest(TestCase):
    def setUp(self):
        self.conn = ConexaoEventos()
        self.eventos = EventoRepository(self.conn)
        self.relacionamentos = EntityRelationshipRepository(self.conn)

    def test_mesma_publicacao_e_numero_evento_retorna_mesmo_id(self):
        primeiro_id = self.eventos.salvar_evento(EVENTO, 100, 1, "2026-01-01")
        segundo_id = self.eventos.salvar_evento(EVENTO, 100, 1, "2026-01-01")

        self.assertEqual(primeiro_id, segundo_id)
        self.assertEqual(len(self.conn.eventos), 1)

    def test_campos_atualizados_preservam_id_e_null_nao_apaga_valor(self):
        primeiro_id = self.eventos.salvar_evento(EVENTO, 100, 1, "2026-01-01")
        revisado = {
            **EVENTO,
            "cargo": "Diretora Geral",
            "agente": {"nome": None},
        }
        segundo_id = self.eventos.salvar_evento(revisado, 100, 1, None)

        self.assertEqual(primeiro_id, segundo_id)
        params = next(iter(self.conn.eventos.values()))["params"]
        self.assertEqual(params[2], "Diretora Geral")
        self.assertEqual(params[1], "Maria da Silva")
        self.assertEqual(params[12], "2026-01-01")

    def test_evento_novo_ou_publicacao_diferente_recebe_id_diferente(self):
        primeiro_id = self.eventos.salvar_evento(EVENTO, 100, 1, "2026-01-01")
        outro_numero = self.eventos.salvar_evento(EVENTO, 100, 2, "2026-01-01")
        outra_publicacao = self.eventos.salvar_evento(EVENTO, 101, 1, "2026-01-01")

        self.assertEqual(len({primeiro_id, outro_numero, outra_publicacao}), 3)

    def test_sql_protege_evento_entidade_e_relacionamento(self):
        self.eventos.relacionar_entidade(1, 2, "AGENTE_PUBLICO")
        self.relacionamentos.criar_relacao(
            2,
            3,
            "NOMEADO_EM",
            diario_id=3279,
            data_publicacao="2026-01-01",
            evento_id=1,
        )

        sql_evento_entidade = self.conn.executed[0][0]
        sql_relacionamento = self.conn.executed[1][0]
        self.assertIn("ON CONFLICT (evento_id, entidade_id, papel) DO NOTHING", sql_evento_entidade)
        self.assertIn("ON CONFLICT (", sql_relacionamento)
        self.assertIn("evento_id", sql_relacionamento)

    def test_salvar_evento_persiste_numero_portaria_gp(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value

        cursor.fetchone.return_value = (123,)

        repository = EventoRepository(conn)

        evento = {
            "tipo_evento": "NOMEACAO",
            "agente": {
                "nome": "JOÃO DA SILVA",
            },
            "numero_portaria_gp": "100/2026",
            "evidencia": {
                "diario_id": 1,
                "numero_bloco": 1,
                "texto": "PORTARIA GP Nº 100/2026 – NOMEAR JOÃO DA SILVA...",
            },
        }

        evento_id = repository.salvar_evento(
            evento,
            publicacao_id=10,
            numero_evento=1,
        )

        assert evento_id == 123

        sql = cursor.execute.call_args.args[0]
        parametros = cursor.execute.call_args.args[1]

        assert "numero_portaria_gp" in sql
        assert "numero_portaria_gp = COALESCE" in sql
        assert "100/2026" in parametros