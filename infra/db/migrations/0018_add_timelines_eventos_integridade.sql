ALTER TABLE {schema}.timelines_entidades
ADD CONSTRAINT fk_timeline_evento_inicio
FOREIGN KEY (evento_inicio_id)
REFERENCES {schema}.eventos(id)
ON DELETE RESTRICT;

ALTER TABLE {schema}.timelines_entidades
ADD CONSTRAINT fk_timeline_evento_fim
FOREIGN KEY (evento_fim_id)
REFERENCES {schema}.eventos(id)
ON DELETE RESTRICT;

ALTER TABLE {schema}.timelines_entidades
ADD CONSTRAINT uq_timeline_evento_inicio
UNIQUE (evento_inicio_id);