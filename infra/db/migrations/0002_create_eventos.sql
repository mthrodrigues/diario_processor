CREATE TABLE IF NOT EXISTS diario.eventos (

    id BIGSERIAL PRIMARY KEY,

    tipo_evento TEXT NOT NULL,

    agente_nome TEXT,

    cargo TEXT,

    orgao TEXT,

    entidade_origem TEXT,

    entidade_destino TEXT,

    processo TEXT,

    contrato TEXT,

    valor NUMERIC,

    diario_id INTEGER,

    numero_bloco INTEGER,

    evidencia_textual TEXT,

    criado_em TIMESTAMP DEFAULT NOW()
);

-- =========================================================
-- ÍNDICES INVESTIGATIVOS
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_eventos_tipo
ON diario.eventos(tipo_evento);

CREATE INDEX IF NOT EXISTS idx_eventos_agente
ON diario.eventos(agente_nome);

CREATE INDEX IF NOT EXISTS idx_eventos_orgao
ON diario.eventos(orgao);

CREATE INDEX IF NOT EXISTS idx_eventos_diario
ON diario.eventos(diario_id);

CREATE INDEX IF NOT EXISTS idx_eventos_contrato
ON diario.eventos(contrato);

CREATE INDEX IF NOT EXISTS idx_eventos_processo
ON diario.eventos(processo);