CREATE TABLE IF NOT EXISTS {schema}.publicacao_contratos (
    id BIGSERIAL PRIMARY KEY,

    publicacao_id BIGINT NOT NULL
        REFERENCES {schema}.publicacoes(id)
        ON DELETE CASCADE,

    contrato_id BIGINT NULL
        REFERENCES {schema}.contratos(id),

    contrato_texto TEXT NOT NULL,
    tipo_instrumento TEXT NOT NULL,
    contexto_documental TEXT NOT NULL,
    evidencia_textual TEXT NOT NULL,
    ordem_no_texto INTEGER NOT NULL,

    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_publicacao_contratos_ordem
        UNIQUE (publicacao_id, ordem_no_texto)
);

CREATE INDEX IF NOT EXISTS idx_diario_publicacao_contratos_publicacao
ON {schema}.publicacao_contratos (publicacao_id);

CREATE INDEX IF NOT EXISTS idx_diario_publicacao_contratos_contrato
ON {schema}.publicacao_contratos (contrato_id);