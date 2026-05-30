-- ============================================================
--  Entrepôt de Données — Embouteillages Douala
--  Script d'initialisation automatique au démarrage PostgreSQL
-- ============================================================

-- Schémas (couches logiques de l'entrepôt)
CREATE SCHEMA IF NOT EXISTS staging;    -- Données brutes nettoyées
CREATE SCHEMA IF NOT EXISTS warehouse;  -- Tables Kimball (dims + faits)
CREATE SCHEMA IF NOT EXISTS datamart;   -- Agrégats pour dashboards BI

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

DO $$
BEGIN
  RAISE NOTICE '✅ DWH Douala initialisé — schémas : staging, warehouse, datamart';
END $$;
