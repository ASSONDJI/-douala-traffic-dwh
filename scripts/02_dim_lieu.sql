
--  DIM_LIEU — Dimension Lieu (Segments de route à Douala)
--  Type SCD : 2 (on garde l'historique si un segment change)
--  Source : OpenStreetMap (données réelles)
--  Grain : 1 enregistrement par segment de route actif


CREATE TABLE IF NOT EXISTS warehouse.dim_lieu (
    -- Clé surrogate (générée automatiquement)
    id_lieu             SERIAL          PRIMARY KEY,
    
    -- Clé naturelle (identifiant OSM du segment)
    code_segment        VARCHAR(50)     NOT NULL,

    -- Localisation géographique (données OSM réelles)
    nom_segment         VARCHAR(200)    NOT NULL,
    -- ex: 'Boulevard de la Liberté - Section Akwa'
    
    axe_principal       VARCHAR(150)    NOT NULL,
    -- ex: 'Boulevard de la Liberté', 'Axe Ndokoti-Bonabéri'
    
    quartier            VARCHAR(100)    NOT NULL,
    -- ex: 'Akwa', 'Ndokoti', 'Bonabéri', 'Bassa', 'Deido'
    
    arrondissement      VARCHAR(100)    NOT NULL,
    -- ex: 'Douala 1er', 'Douala 2e', 'Douala 3e', 'Douala 4e', 'Douala 5e'
    
    commune             VARCHAR(100)    NOT NULL DEFAULT 'Douala',
    region              VARCHAR(50)     NOT NULL DEFAULT 'Littoral',
    pays                VARCHAR(50)     NOT NULL DEFAULT 'Cameroun',

    -- Coordonnées GPS (point central du segment)
    latitude_debut      DECIMAL(10,7),
    longitude_debut     DECIMAL(10,7),
    latitude_fin        DECIMAL(10,7),
    longitude_fin       DECIMAL(10,7),
    latitude_centre     DECIMAL(10,7),
    longitude_centre    DECIMAL(10,7),

    -- Caractéristiques physiques du segment
    longueur_km         DECIMAL(8,3)    NOT NULL,
    nombre_voies        SMALLINT        NOT NULL DEFAULT 2,
    type_route          VARCHAR(50)     NOT NULL,
    -- Valeurs : 'Voie rapide', 'Avenue principale',
    --           'Rue secondaire', 'Piste', 'Pont'
    
    capacite_vehicules_h INT,
    -- Capacité théorique en véhicules/heure

    -- Caractéristiques locales importantes pour l'analyse
    a_feux_circulation  BOOLEAN         NOT NULL DEFAULT FALSE,
    a_rond_point        BOOLEAN         NOT NULL DEFAULT FALSE,
    est_pont            BOOLEAN         NOT NULL DEFAULT FALSE,
    -- ex: Pont sur le Wouri
    
    est_axe_critique    BOOLEAN         NOT NULL DEFAULT FALSE,
    -- TRUE pour Ndokoti, Bonabéri, Bvd Liberté (axes les plus chargés)
    
    zone_type           VARCHAR(50),
    -- Valeurs : 'Centre commercial', 'Zone industrielle',
    --           'Zone résidentielle', 'Périphérie', 'Marché'

    -- SCD Type 2 — gestion des changements historiques
    date_debut_validite DATE            NOT NULL DEFAULT CURRENT_DATE,
    date_fin_validite   DATE,
    -- NULL = enregistrement actuel
    
    est_actif           BOOLEAN         NOT NULL DEFAULT TRUE,
    version             SMALLINT        NOT NULL DEFAULT 1,

    -- Métadonnées
    source_donnee       VARCHAR(50)     NOT NULL DEFAULT 'OpenStreetMap',
    date_chargement     TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_lieu_code      ON warehouse.dim_lieu(code_segment);
CREATE INDEX IF NOT EXISTS idx_dim_lieu_quartier  ON warehouse.dim_lieu(quartier);
CREATE INDEX IF NOT EXISTS idx_dim_lieu_axe       ON warehouse.dim_lieu(axe_principal);
CREATE INDEX IF NOT EXISTS idx_dim_lieu_actif     ON warehouse.dim_lieu(est_actif);
CREATE INDEX IF NOT EXISTS idx_dim_lieu_critique  ON warehouse.dim_lieu(est_axe_critique);

COMMENT ON TABLE warehouse.dim_lieu IS
'Dimension géographique — segments de route à Douala.
SCD Type 2 : conservation de l''historique des modifications.
Alimentée par les données OpenStreetMap réelles de Douala.';

SELECT 'DIM_LIEU créée ' AS statut;
