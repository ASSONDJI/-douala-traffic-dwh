-- ============================================================
--  DIM_CAPTEUR — Dimension Source de Mesure
--  Type SCD : 2
--  Représente les "capteurs" virtuels ou réels qui mesurent
--  le trafic (API GPS, simulation, caméra, etc.)
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_capteur (
    id_capteur              SERIAL      PRIMARY KEY,
    
    code_capteur            VARCHAR(50) NOT NULL UNIQUE,
    nom_capteur             VARCHAR(150) NOT NULL,
    
    type_capteur            VARCHAR(50) NOT NULL,
    -- Valeurs : 'API_GPS', 'SIMULATION', 'CAMERA', 'BOUCLE_INDUCTIVE'
    
    source_donnee           VARCHAR(100) NOT NULL,
    -- ex: 'OpenStreetMap', 'Open-Meteo API', 'Générateur Python'
    
    -- Localisation du capteur
    latitude                DECIMAL(10,7),
    longitude               DECIMAL(10,7),
    lieu_installation       VARCHAR(200),

    -- Qualité de la donnée
    fiabilite_pct           SMALLINT    NOT NULL DEFAULT 95
                            CHECK (fiabilite_pct BETWEEN 0 AND 100),
    frequence_mesure_min    SMALLINT    NOT NULL DEFAULT 5,
    -- Fréquence de mesure en minutes

    est_actif               BOOLEAN     NOT NULL DEFAULT TRUE,
    
    -- SCD Type 2
    date_debut_validite     DATE        NOT NULL DEFAULT CURRENT_DATE,
    date_fin_validite       DATE,
    version                 SMALLINT    NOT NULL DEFAULT 1,

    date_chargement         TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Capteurs de référence (sources réelles du projet)
INSERT INTO warehouse.dim_capteur
    (code_capteur, nom_capteur, type_capteur,
     source_donnee, fiabilite_pct, frequence_mesure_min)
VALUES
    ('OSM_API',    'OpenStreetMap API',      'API_GPS',    'OpenStreetMap',   90, 5),
    ('METEO_API',  'Open-Meteo API Douala',  'API_METEO',  'Open-Meteo',      95, 60),
    ('SIM_PYTHON', 'Générateur Python',      'SIMULATION', 'Script Python',   85, 5),
    ('INCONNU',    'Source inconnue',        'INCONNU',    'Indéterminé',     50, 5)
ON CONFLICT (code_capteur) DO NOTHING;

COMMENT ON TABLE warehouse.dim_capteur IS
'Dimension source de mesure. Permet de tracer la lignée des données
(data lineage) : savoir quelle source a produit chaque mesure.
Essentiel pour la gouvernance des données.';

SELECT 'DIM_CAPTEUR créée et peuplée ✅' AS statut;
