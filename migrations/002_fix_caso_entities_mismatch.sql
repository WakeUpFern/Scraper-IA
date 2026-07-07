-- Migration: Add missing EF Core mapping columns to case tables in naat_db2
-- Resolves DB mismatches for CasoPersona, CasoIdentidadDigital, and CasoAnalisis

ALTER TABLE casos.caso_persona ADD COLUMN IF NOT EXISTS fecha_desvinculacion timestamp without time zone;
ALTER TABLE casos.caso_identidad_digital ADD COLUMN IF NOT EXISTS fecha_desvinculacion timestamp without time zone;
ALTER TABLE casos.caso_analisis ADD COLUMN IF NOT EXISTS fecha_desvinculacion timestamp without time zone;
ALTER TABLE casos.caso_analisis ADD COLUMN IF NOT EXISTS estado character varying(50) NOT NULL DEFAULT 'Activo';
