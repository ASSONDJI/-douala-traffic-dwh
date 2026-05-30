--  DIM_EVENEMENT — Dimension Événement
--  Type SCD : 1
--  Regroupe : météo, manifestations, matchs, marchés, accidents
--  Conformément à la décision de conception : la météo est
--  un TYPE d'événement (pas une dimension séparée)


CREATE TABLE IF NOT EXISTS warehouse.dim_evenement (
    id_evenement        SERIAL          PRIMARY KEY,
    
    -- Classification de l'événement
    type_evenement      VARCHAR(50)     NOT NULL,
    -- Valeurs : 'METEO', 'SPORT', 'MANIFESTATION',
    --           'MARCHE', 'TRAVAUX', 'ACCIDENT', 'FETE', 'NORMAL'
    
    sous_type           VARCHAR(100)    NOT NULL,
    -- ex: pour METEO → 'Pluie forte', 'Orage', 'Brouillard', 'Ensoleillé'
    -- ex: pour SPORT → 'Match Lions Indomptables', 'Match local'
    -- ex: pour MARCHE → 'Marché Mboppi', 'Marché central'
    
    nom_evenement       VARCHAR(200)    NOT NULL,
    description         TEXT,

    -- Impact sur le trafic (cœur de l'analyse)
    impact_trafic       VARCHAR(20)     NOT NULL DEFAULT 'NEUTRE',
    -- Valeurs : 'AMELIORATION', 'NEUTRE', 'DEGRADATION_FAIBLE',
    --           'DEGRADATION_MODEREE', 'DEGRADATION_SEVERE', 'BLOQUANT'
    
    coefficient_impact  DECIMAL(4,2)    NOT NULL DEFAULT 1.0,
    -- Multiplicateur sur l'indice de congestion
    -- 1.0 = neutre, 1.5 = +50% congestion, 0.8 = -20% (amélioration)

    -- Paramètres météo (remplis uniquement si type_evenement = 'METEO')
    intensite_pluie_mm  DECIMAL(6,2),   -- mm/heure
    temperature_c       DECIMAL(5,2),
    humidite_pct        SMALLINT,
    vitesse_vent_kmh    DECIMAL(5,2),
    condition_visibilite VARCHAR(20),
    -- Valeurs : 'EXCELLENTE', 'BONNE', 'MODEREE', 'FAIBLE', 'TRES_FAIBLE'

    -- Localisation de l'événement
    lieu_evenement      VARCHAR(200),
    -- ex: 'Stade de la Réunification', 'Marché Mboppi', 'Centre-ville'
    
    rayon_impact_km     DECIMAL(5,2),
    -- Zone d'influence de l'événement sur le trafic

    -- Enregistrement "aucun événement" (dimension dégénérée)
    est_evenement_normal BOOLEAN        NOT NULL DEFAULT FALSE,
    -- TRUE pour l'enregistrement de référence "Pas d'événement"

    date_chargement     TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Enregistrements de référence (toujours présents)
INSERT INTO warehouse.dim_evenement
    (type_evenement, sous_type, nom_evenement,
     impact_trafic, coefficient_impact, est_evenement_normal)
VALUES
    -- Enregistrement neutre (référence)
    ('NORMAL',        'Aucun',          'Aucun événement particulier',
     'NEUTRE', 1.0, TRUE),
    
    -- Météo favorable
    ('METEO',         'Ensoleillé',     'Temps ensoleillé',
     'NEUTRE', 1.0, FALSE),
    ('METEO',         'Nuageux',        'Temps nuageux sans pluie',
     'NEUTRE', 1.0, FALSE),

    -- Météo défavorable (critique à Douala !)
    ('METEO',         'Pluie légère',   'Pluie légère',
     'DEGRADATION_FAIBLE',    1.2, FALSE),
    ('METEO',         'Pluie forte',    'Pluie forte',
     'DEGRADATION_MODEREE',   1.6, FALSE),
    ('METEO',         'Orage',          'Orage violent',
     'DEGRADATION_SEVERE',    2.0, FALSE),
    ('METEO',         'Inondation',     'Inondation / Voie submergée',
     'BLOQUANT',              3.0, FALSE),

    -- Événements sportifs
    ('SPORT',         'Match Lions',    'Match Lions Indomptables (stade)',
     'DEGRADATION_SEVERE',    1.8, FALSE),
    ('SPORT',         'Match local',    'Match de football local',
     'DEGRADATION_MODEREE',   1.4, FALSE),

    -- Marchés (très impactants à Douala)
    ('MARCHE',        'Marché Mboppi',  'Jour de grand marché Mboppi',
     'DEGRADATION_MODEREE',   1.5, FALSE),
    ('MARCHE',        'Marché central', 'Marché central de Douala',
     'DEGRADATION_MODEREE',   1.4, FALSE),

    -- Travaux / Incidents
    ('TRAVAUX',       'Voirie',         'Travaux sur voie',
     'DEGRADATION_MODEREE',   1.5, FALSE),
    ('ACCIDENT',      'Accident',       'Accident de circulation',
     'DEGRADATION_SEVERE',    1.9, FALSE),

    -- Fêtes et manifestations
    ('FETE',          'Fête nationale', '20 Mai — Fête Nationale Cameroun',
     'DEGRADATION_SEVERE',    1.7, FALSE),
    ('MANIFESTATION', 'Cortège',        'Cortège officiel / Défilé',
     'BLOQUANT',              2.5, FALSE)

ON CONFLICT DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_dim_evenement_type   ON warehouse.dim_evenement(type_evenement);
CREATE INDEX IF NOT EXISTS idx_dim_evenement_impact ON warehouse.dim_evenement(impact_trafic);

COMMENT ON TABLE warehouse.dim_evenement IS
'Dimension événement — regroupe météo, sport, marchés, travaux, accidents.
La météo est un sous-type d''événement (choix de conception justifié
par la simplicité du modèle et la recommandation de l''enseignant).';

SELECT 'DIM_EVENEMENT créée et peuplée ' AS statut;
