CREATE TABLE IF NOT EXISTS {schema}.publicacao_processos (
    id BIGSERIAL PRIMARY KEY,

    publicacao_id BIGINT NOT NULL
        REFERENCES {schema}.publicacoes(id)
        ON DELETE CASCADE,

    processo_id BIGINT NOT NULL
        REFERENCES {schema}.processos(id),

    evidencia_textual TEXT NOT NULL,
    ordem_no_texto INTEGER NOT NULL,

    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_publicacao_processos_ordem
        UNIQUE (publicacao_id, ordem_no_texto)
);

CREATE INDEX IF NOT EXISTS idx_diario_publicacao_processos_publicacao
ON {schema}.publicacao_processos (publicacao_id);

CREATE INDEX IF NOT EXISTS idx_diario_publicacao_processos_processo
ON {schema}.publicacao_processos (processo_id);