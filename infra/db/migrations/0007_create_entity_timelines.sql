CREATE TABLE IF NOT EXISTS diario.entity_timelines (

    id BIGSERIAL PRIMARY KEY,

    entidade_id BIGINT NOT NULL,

    orgao_entidade_id BIGINT,

    tipo_vinculo TEXT NOT NULL,

    data_inicio DATE,
    data_fim DATE,

    ativo BOOLEAN DEFAULT TRUE,

    evento_inicio_id BIGINT,
    evento_fim_id BIGINT,

    criado_em TIMESTAMP DEFAULT NOW()

);

-- =========================================================
-- ÍNDICES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_timeline_entidade
ON diario.entity_timelines(entidade_id);

CREATE INDEX IF NOT EXISTS idx_timeline_orgao
ON diario.entity_timelines(orgao_entidade_id);

CREATE INDEX IF NOT EXISTS idx_timeline_ativo
ON diario.entity_timelines(ativo);

CREATE INDEX IF NOT EXISTS idx_timeline_datas
ON diario.entity_timelines(data_inicio, data_fim);