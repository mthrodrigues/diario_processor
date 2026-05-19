CREATE TABLE IF NOT EXISTS diario.entidades (

    id BIGSERIAL PRIMARY KEY,

    tipo_entidade TEXT NOT NULL,

    nome_original TEXT NOT NULL,

    nome_normalizado TEXT NOT NULL,

    criado_em TIMESTAMP DEFAULT NOW()
);

-- =========================================================
-- ÍNDICES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_entidades_tipo
ON diario.entidades(tipo_entidade);

CREATE INDEX IF NOT EXISTS idx_entidades_nome_normalizado
ON diario.entidades(nome_normalizado);

-- =========================================================
-- UNIQUE SEMÂNTICO
-- =========================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_entidade_unica
ON diario.entidades(tipo_entidade, nome_normalizado);