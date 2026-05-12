CREATE TABLE IF NOT EXISTS diario.entity_relationships (

    id BIGSERIAL PRIMARY KEY,

    entidade_origem_id BIGINT NOT NULL,
    entidade_destino_id BIGINT NOT NULL,

    tipo_relacao TEXT NOT NULL,

    diario_id INTEGER,

    data_publicacao DATE,

    criado_em TIMESTAMP DEFAULT NOW()

);

-- =========================================================
-- ÍNDICES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_entity_rel_origem
ON diario.entity_relationships(entidade_origem_id);

CREATE INDEX IF NOT EXISTS idx_entity_rel_destino
ON diario.entity_relationships(entidade_destino_id);

CREATE INDEX IF NOT EXISTS idx_entity_rel_tipo
ON diario.entity_relationships(tipo_relacao);

CREATE INDEX IF NOT EXISTS idx_entity_rel_data
ON diario.entity_relationships(data_publicacao);