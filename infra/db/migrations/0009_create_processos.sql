CREATE TABLE IF NOT EXISTS {schema}.processos (
    id BIGSERIAL PRIMARY KEY,
    processo TEXT NOT NULL,
    processo_normalizado TEXT NOT NULL UNIQUE,
    data_primeira_publicacao DATE,
    data_ultima_publicacao DATE,
    quantidade_publicacoes INTEGER NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_diario_processos_processo_normalizado
ON {schema}.processos (processo_normalizado);
