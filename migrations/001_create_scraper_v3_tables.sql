-- Migración inicial para Scr4per v3 MVP
-- Crea las tablas de auditoría, evidencia, observación de identidad y snapshot del grafo técnico en naat_db2.

CREATE TABLE IF NOT EXISTS redes.tool_run (
  id_tool_run bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_usuario bigint REFERENCES entidades.usuario(id_usuario),
  tool_name varchar(150) NOT NULL,
  platform varchar(50),
  input_json jsonb NOT NULL DEFAULT '{}',
  output_json jsonb NOT NULL DEFAULT '{}',
  status varchar(50) NOT NULL,
  error text,
  started_at timestamp NOT NULL DEFAULT current_timestamp,
  finished_at timestamp,
  cost_json jsonb NOT NULL DEFAULT '{}',
  extractor_strategy varchar(100),
  parser_version varchar(50),
  created_by_agent boolean DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_tool_run_analisis ON redes.tool_run(id_analisis);

CREATE TABLE IF NOT EXISTS redes.raw_evidence (
  id_raw_evidence bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_tool_run bigint REFERENCES redes.tool_run(id_tool_run) ON DELETE SET NULL,
  evidence_type varchar(50) NOT NULL,
  platform varchar(50),
  source_url text,
  request_hash varchar(255),
  operation_name varchar(255),
  storage_path text,
  raw_json jsonb,
  metadata jsonb DEFAULT '{}',
  observed_at timestamp NOT NULL DEFAULT current_timestamp
);

CREATE INDEX IF NOT EXISTS idx_raw_evidence_tool_run ON redes.raw_evidence(id_tool_run);

CREATE TABLE IF NOT EXISTS redes.identidad_observacion (
  id_identidad_observacion bigserial PRIMARY KEY,
  id_analisis bigint NOT NULL REFERENCES redes.analisis(id_analisis),
  id_tool_run bigint REFERENCES redes.tool_run(id_tool_run) ON DELETE SET NULL,
  id_identidad_digital bigint REFERENCES personas.identidad_digital(id_identidad_digital),
  id_usuario_observador bigint REFERENCES entidades.usuario(id_usuario),
  id_caso bigint REFERENCES casos.caso(id_caso),
  nombre_publico_observado varchar(150),
  username_observado varchar(150),
  usuario_url_observada text,
  descripcion_observada text,
  foto_url_observada text,
  metricas_json jsonb DEFAULT '{}',
  raw_json jsonb DEFAULT '{}',
  observed_at timestamp NOT NULL DEFAULT current_timestamp
);

CREATE INDEX IF NOT EXISTS idx_identidad_observacion_analisis ON redes.identidad_observacion(id_analisis);

CREATE TABLE IF NOT EXISTS redes.graph_snapshot (
  id_graph_snapshot bigserial PRIMARY KEY,
  id_analisis bigint REFERENCES redes.analisis(id_analisis),
  id_caso bigint REFERENCES casos.caso(id_caso),
  id_usuario bigint REFERENCES entidades.usuario(id_usuario),
  graph_scope varchar(50) NOT NULL,
  graph_json jsonb NOT NULL,
  metrics_json jsonb DEFAULT '{}',
  storage_path text,
  fecha_creacion timestamp DEFAULT current_timestamp
);

CREATE INDEX IF NOT EXISTS idx_graph_snapshot_analisis ON redes.graph_snapshot(id_analisis);
