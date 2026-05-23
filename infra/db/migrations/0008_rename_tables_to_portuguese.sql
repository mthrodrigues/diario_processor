-- =========================================================
-- RENOMEIA TABELAS
-- =========================================================

ALTER TABLE diario.entity_relationships
RENAME TO relacionamentos_entidades;

ALTER TABLE diario.entity_timelines
RENAME TO timelines_entidades;

-- =========================================================
-- RENOMEIA ÍNDICES RELACIONAMENTOS
-- =========================================================

ALTER INDEX IF EXISTS diario.idx_entity_rel_origem
RENAME TO idx_rel_entidades_origem;

ALTER INDEX IF EXISTS diario.idx_entity_rel_destino
RENAME TO idx_rel_entidades_destino;

ALTER INDEX IF EXISTS diario.idx_entity_rel_tipo
RENAME TO idx_rel_entidades_tipo;

ALTER INDEX IF EXISTS diario.idx_entity_rel_data
RENAME TO idx_rel_entidades_data;

-- =========================================================
-- RENOMEIA ÍNDICES TIMELINES
-- =========================================================

ALTER INDEX IF EXISTS diario.idx_timeline_entidade
RENAME TO idx_timelines_entidade;

ALTER INDEX IF EXISTS diario.idx_timeline_orgao
RENAME TO idx_timelines_orgao;

ALTER INDEX IF EXISTS diario.idx_timeline_ativo
RENAME TO idx_timelines_ativo;

ALTER INDEX IF EXISTS diario.idx_timeline_datas
RENAME TO idx_timelines_datas;