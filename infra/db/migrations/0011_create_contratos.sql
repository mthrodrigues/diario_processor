CREATE TABLE IF NOT EXISTS {schema}.contratos (
    id BIGSERIAL PRIMARY KEY,
    contrato TEXT NOT NULL,
    contrato_normalizado TEXT NOT NULL UNIQUE,
    data_primeira_publicacao DATE,
    data_ultima_publicacao DATE,
    quantidade_publicacoes INTEGER NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_diario_contratos_contrato_normalizado
ON {schema}.contratos (contrato_normalizado);
