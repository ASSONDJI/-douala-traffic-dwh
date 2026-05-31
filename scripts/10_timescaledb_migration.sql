-- ============================================================
--  TIMESCALEDB — Migration et optimisation
--  fait_embouteillage convertie en hypertable
--  Chunk interval : 7 jours
--  Compression : activée après 30 jours
-- ============================================================

-- Prérequis : shared_preload_libraries = 'timescaledb'
-- dans postgresql.conf

-- 1. Activer l'extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 2. Ajouter colonne timestamp
ALTER TABLE warehouse.fait_embouteillage
    ADD COLUMN IF NOT EXISTS ts TIMESTAMPTZ;

UPDATE warehouse.fait_embouteillage f
SET ts = t.date_heure
FROM warehouse.dim_temps t
WHERE f.id_temps = t.id_temps;

-- 3. Recréer la clé primaire avec ts
ALTER TABLE warehouse.fait_embouteillage
    DROP CONSTRAINT fait_embouteillage_pkey;

ALTER TABLE warehouse.fait_embouteillage
    ADD PRIMARY KEY (id_fait, ts);

-- 4. Convertir en hypertable (chunks de 7 jours)
SELECT create_hypertable(
    'warehouse.fait_embouteillage',
    'ts',
    chunk_time_interval => INTERVAL '7 days',
    migrate_data => true
);

-- 5. Activer la compression (données > 30 jours)
ALTER TABLE warehouse.fait_embouteillage
    SET (
        timescaledb.compress,
        timescaledb.compress_segmentby = 'id_lieu',
        timescaledb.compress_orderby = 'ts DESC'
    );

SELECT add_compression_policy(
    'warehouse.fait_embouteillage',
    INTERVAL '30 days'
);

-- 6. Vérification
SELECT chunk_name, range_start, range_end
FROM timescaledb_information.chunks
WHERE hypertable_name = 'fait_embouteillage'
ORDER BY range_start;
