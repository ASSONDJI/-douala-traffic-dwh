-- ============================================================
--  DIM_TEMPS — Dimension Temps
--  Type SCD : 0 (statique — le temps ne change jamais)
--  Grain : 1 enregistrement par tranche de 5 minutes
--  Couvre : 2020-01-01 → 2026-12-31
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_temps (
    -- Clé surrogate (format : YYYYMMDDHH24MI → ex: 202401150730)
    id_temps            BIGINT          PRIMARY KEY,

    -- Date complète
    date_complete       DATE            NOT NULL,
    date_heure          TIMESTAMP       NOT NULL,

    -- Décomposition temporelle
    annee               SMALLINT        NOT NULL,
    trimestre           SMALLINT        NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    mois                SMALLINT        NOT NULL CHECK (mois BETWEEN 1 AND 12),
    nom_mois            VARCHAR(20)     NOT NULL,
    semaine_annee       SMALLINT        NOT NULL,
    jour_mois           SMALLINT        NOT NULL CHECK (jour_mois BETWEEN 1 AND 31),
    jour_semaine        SMALLINT        NOT NULL CHECK (jour_semaine BETWEEN 0 AND 6),
    nom_jour            VARCHAR(20)     NOT NULL,
    heure               SMALLINT        NOT NULL CHECK (heure BETWEEN 0 AND 23),
    minute              SMALLINT        NOT NULL CHECK (minute IN (0,5,10,15,20,25,30,35,40,45,50,55)),

    -- Indicateurs analytiques (très utiles pour les requêtes OLAP)
    est_weekend         BOOLEAN         NOT NULL DEFAULT FALSE,
    est_jour_ferie_cm   BOOLEAN         NOT NULL DEFAULT FALSE,
    nom_jour_ferie      VARCHAR(100),   -- ex: 'Fête Nationale Cameroun'
    
    -- Tranches horaires (spécifiques à Douala)
    tranche_horaire     VARCHAR(30)     NOT NULL,
    -- Valeurs : 'Pointe matin (6h-9h)', 'Journée (9h-17h)',
    --           'Pointe soir (17h-20h)', 'Nuit (20h-6h)'
    
    est_heure_pointe    BOOLEAN         NOT NULL DEFAULT FALSE,
    
    -- Saison (contexte camerounais)
    saison_cameroun     VARCHAR(30)     NOT NULL,
    -- Valeurs : 'Grande saison sèche (Nov-Mar)',
    --           'Grande saison pluies (Jul-Oct)',
    --           'Petite saison sèche (Avr-Juin)'

    -- Métadonnées
    date_creation       TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Index pour accélérer les requêtes analytiques fréquentes
CREATE INDEX IF NOT EXISTS idx_dim_temps_date     ON warehouse.dim_temps(date_complete);
CREATE INDEX IF NOT EXISTS idx_dim_temps_heure    ON warehouse.dim_temps(heure);
CREATE INDEX IF NOT EXISTS idx_dim_temps_pointe   ON warehouse.dim_temps(est_heure_pointe);
CREATE INDEX IF NOT EXISTS idx_dim_temps_weekend  ON warehouse.dim_temps(est_weekend);
CREATE INDEX IF NOT EXISTS idx_dim_temps_ferie    ON warehouse.dim_temps(est_jour_ferie_cm);

COMMENT ON TABLE warehouse.dim_temps IS 
'Dimension temporelle — grain : 5 minutes. Couvre 2020-2026.
Inclut les spécificités camerounaises : jours fériés officiels,
saisons climatiques de Douala, heures de pointe locales.';

SELECT 'DIM_TEMPS créée ✅' AS statut;
