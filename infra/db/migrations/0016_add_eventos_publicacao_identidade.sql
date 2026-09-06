ALTER TABLE {schema}.eventos
ADD COLUMN publicacao_id BIGINT;

ALTER TABLE {schema}.eventos
ADD COLUMN numero_evento INTEGER;

ALTER TABLE {schema}.eventos
ADD CONSTRAINT fk_eventos_publicacao
FOREIGN KEY (publicacao_id)
REFERENCES {schema}.publicacoes(id)
ON DELETE CASCADE;

ALTER TABLE {schema}.eventos
ADD CONSTRAINT uq_eventos_publicacao_numero
UNIQUE (publicacao_id, numero_evento);