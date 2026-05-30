--  DIM_VEHICULE — Dimension Type de Véhicule
--  Type SCD : 1 (écrasement simple — les catégories évoluent peu)
--  Spécificité : inclut le Bendskin (moto-taxi), essentiel à Douala


CREATE TABLE IF NOT EXISTS warehouse.dim_vehicule (
    id_vehicule         SERIAL          PRIMARY KEY,
    
    -- Classification
    code_vehicule       VARCHAR(20)     NOT NULL UNIQUE,
    -- ex: 'BENDSKIN', 'TAXI_VILLE', 'BUS', 'CAMION_LOURD'
    
    categorie           VARCHAR(50)     NOT NULL,
    -- ex: 'Deux-roues', 'Véhicule léger', 'Transport commun', 'Poids lourd'
    
    nom_vehicule        VARCHAR(100)    NOT NULL,
    -- ex: 'Bendskin (moto-taxi)', 'Taxi ville', 'Bus urbain'
    
    description         TEXT,

    -- Impact sur le trafic (paramètres de simulation)
    coefficient_pce     DECIMAL(4,2)    NOT NULL DEFAULT 1.0,
    -- PCE = Passenger Car Equivalent (unité standard de trafic)
    -- Bendskin = 0.5, Voiture = 1.0, Bus = 2.5, Camion = 3.5
    
    vitesse_max_urbain_kmh  SMALLINT    NOT NULL DEFAULT 60,
    impact_congestion   VARCHAR(20)     NOT NULL DEFAULT 'MOYEN',
    -- Valeurs : 'FAIBLE', 'MOYEN', 'ELEVE', 'TRES_ELEVE'

    -- Caractéristiques locales Douala
    est_specifique_cameroun BOOLEAN     NOT NULL DEFAULT FALSE,
    -- TRUE pour Bendskin, Clando (taxi clandestin)
    
    est_transport_commun    BOOLEAN     NOT NULL DEFAULT FALSE,
    
    -- SCD Type 1
    date_chargement     TIMESTAMP       NOT NULL DEFAULT NOW(),
    derniere_modification TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- Insertion des données de référence (dimensions statiques)
INSERT INTO warehouse.dim_vehicule 
    (code_vehicule, categorie, nom_vehicule, coefficient_pce,
     vitesse_max_urbain_kmh, impact_congestion, 
     est_specifique_cameroun, est_transport_commun)
VALUES
    ('BENDSKIN',    'Deux-roues',          'Bendskin (moto-taxi)',        0.5,  70, 'FAIBLE',     TRUE,  FALSE),
    ('MOTO_PERSO',  'Deux-roues',          'Moto personnelle',            0.5,  80, 'FAIBLE',     FALSE, FALSE),
    ('TAXI_VILLE',  'Véhicule léger',      'Taxi ville (jaune)',          1.0,  60, 'MOYEN',      FALSE, TRUE),
    ('CLANDO',      'Véhicule léger',      'Taxi clandestin',             1.0,  60, 'MOYEN',      TRUE,  TRUE),
    ('VOITURE',     'Véhicule léger',      'Voiture particulière',        1.0,  80, 'MOYEN',      FALSE, FALSE),
    ('MINIBUS',     'Transport commun',    'Minibus (Hiace)',              2.0,  60, 'ELEVE',      FALSE, TRUE),
    ('BUS_URBAIN',  'Transport commun',    'Bus urbain',                  2.5,  50, 'ELEVE',      FALSE, TRUE),
    ('CAMION_LEGER','Poids lourd',         'Camion léger / Pickup',       2.0,  70, 'ELEVE',      FALSE, FALSE),
    ('CAMION_LOURD','Poids lourd',         'Camion lourd / Semi-remorque',3.5,  50, 'TRES_ELEVE', FALSE, FALSE),
    ('INCONNU',     'Non classifié',       'Type inconnu',                1.0,  60, 'MOYEN',      FALSE, FALSE)
ON CONFLICT (code_vehicule) DO NOTHING;

COMMENT ON TABLE warehouse.dim_vehicule IS
'Dimension type de véhicule. Inclut les spécificités de Douala :
Bendskin (moto-taxi omniprésent), Clando (taxi clandestin).
Le coefficient PCE permet de normaliser les volumes de trafic.';

SELECT 'DIM_VEHICULE créée et peuplée ' AS statut;
