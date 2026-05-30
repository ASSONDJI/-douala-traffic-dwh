-- ============================================================
--  FAIT_EMBOUTEILLAGE — Table de Faits Centrale
--  Méthodologie : Kimball — Transaction Grain
--  Grain : 1 mesure de trafic par segment × par tranche de 5 min
--
--  Justification du grain :
--  "Le grain atomique de 5 minutes permet toutes les agrégations
--   analytiques (roll-up horaire, journalier, mensuel) via OLAP,
--   tout en capturant les variations rapides caractéristiques
--   du trafic urbain de Douala." — Kimball, The DW Toolkit
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.fait_embouteillage (

    -- ── Clé surrogate ────────────────────────────────────────
    id_fait             BIGSERIAL       PRIMARY KEY,

    -- ── Clés étrangères (liens vers les 6 dimensions) ────────
    id_temps            BIGINT          NOT NULL
                        REFERENCES warehouse.dim_temps(id_temps),

    id_lieu             INT             NOT NULL
                        REFERENCES warehouse.dim_lieu(id_lieu),

    id_vehicule         INT             NOT NULL
                        REFERENCES warehouse.dim_vehicule(id_vehicule),

    id_evenement        INT             NOT NULL
                        REFERENCES warehouse.dim_evenement(id_evenement),

    id_trajet           INT
                        REFERENCES warehouse.dim_trajet(id_trajet),
    -- Nullable : une mesure ponctuelle peut ne pas avoir de trajet associé

    id_capteur          INT             NOT NULL
                        REFERENCES warehouse.dim_capteur(id_capteur),

    -- ── Mesures de volume ────────────────────────────────────
    volume_vehicules        INT         NOT NULL CHECK (volume_vehicules >= 0),
    -- Nombre de véhicules comptés sur le segment pendant 5 min

    volume_pce              DECIMAL(10,2) NOT NULL,
    -- Volume converti en PCE (Passenger Car Equivalent)
    -- Normalise les différents types de véhicules

    densite_vehicules_km    DECIMAL(10,3),
    -- Véhicules par km de route (densité)

    -- ── Mesures de vitesse ───────────────────────────────────
    vitesse_moyenne_kmh     DECIMAL(8,2) NOT NULL CHECK (vitesse_moyenne_kmh >= 0),
    -- Vitesse moyenne observée des véhicules

    vitesse_libre_kmh       DECIMAL(8,2) NOT NULL CHECK (vitesse_libre_kmh > 0),
    -- Vitesse de référence sans congestion (constante par segment)

    -- ── Indicateurs de congestion (métriques calculées) ──────
    indice_congestion       DECIMAL(8,4) NOT NULL,
    -- Formule : vitesse_libre ÷ vitesse_moyenne
    -- 1.0 = fluide | 2.0 = 2× plus lent | >4.0 = embouteillage sévère

    niveau_service          CHAR(1)      NOT NULL CHECK (niveau_service IN ('A','B','C','D','E','F')),
    -- LOS (Level of Service) — standard HCM (Highway Capacity Manual)
    -- A = libre (>90% vitesse libre)
    -- B = légèrement chargé (70-90%)
    -- C = stable mais chargé (50-70%)
    -- D = instable (40-50%)
    -- E = saturé (30-40%)
    -- F = bloqué (<30% vitesse libre)

    longueur_bouchon_km     DECIMAL(8,3) NOT NULL DEFAULT 0,
    -- Longueur estimée de la file d'attente

    -- ── Mesures de temps ─────────────────────────────────────
    temps_parcours_min      DECIMAL(8,2) NOT NULL,
    -- Temps réel pour traverser le segment

    temps_reference_min     DECIMAL(8,2) NOT NULL,
    -- Temps sans congestion (référence)

    delai_supplementaire_min DECIMAL(8,2) NOT NULL DEFAULT 0,
    -- = temps_parcours - temps_reference (temps perdu)

    -- ── Indicateurs incidents ─────────────────────────────────
    flag_incident           BOOLEAN      NOT NULL DEFAULT FALSE,
    -- TRUE si accident ou incident signalé

    flag_donnee_manquante   BOOLEAN      NOT NULL DEFAULT FALSE,
    -- TRUE si donnée imputée / interpolée (qualité données)

    -- ── Métadonnées ETL ───────────────────────────────────────
    date_chargement         TIMESTAMP    NOT NULL DEFAULT NOW(),
    batch_id                VARCHAR(50),
    -- Identifiant du batch ETL qui a chargé cet enregistrement

    CONSTRAINT chk_indice_positif CHECK (indice_congestion > 0),
    CONSTRAINT chk_delai_positif  CHECK (delai_supplementaire_min >= 0)
);

-- ── Index d'optimisation des requêtes OLAP ───────────────────
-- Ces index accélèrent les roll-up, drill-down, slice et dice

CREATE INDEX IF NOT EXISTS idx_fait_temps
    ON warehouse.fait_embouteillage(id_temps);

CREATE INDEX IF NOT EXISTS idx_fait_lieu
    ON warehouse.fait_embouteillage(id_lieu);

CREATE INDEX IF NOT EXISTS idx_fait_evenement
    ON warehouse.fait_embouteillage(id_evenement);

CREATE INDEX IF NOT EXISTS idx_fait_vehicule
    ON warehouse.fait_embouteillage(id_vehicule);

CREATE INDEX IF NOT EXISTS idx_fait_niveau_service
    ON warehouse.fait_embouteillage(niveau_service);

CREATE INDEX IF NOT EXISTS idx_fait_congestion
    ON warehouse.fait_embouteillage(indice_congestion);

-- Index composite (requêtes les plus fréquentes)
CREATE INDEX IF NOT EXISTS idx_fait_temps_lieu
    ON warehouse.fait_embouteillage(id_temps, id_lieu);

CREATE INDEX IF NOT EXISTS idx_fait_incident
    ON warehouse.fait_embouteillage(flag_incident) WHERE flag_incident = TRUE;

COMMENT ON TABLE warehouse.fait_embouteillage IS
'Table de faits centrale — Entrepôt Embouteillages Douala.
Grain : 1 mesure de trafic par segment de route, par tranche de 5 minutes.
Méthodologie Kimball — Transaction Grain.
Contient toutes les métriques nécessaires aux opérations OLAP :
roll-up (5min→heure→jour→mois), drill-down, slice (par pluie),
dice (pluie + vendredi + Ndokoti).';

SELECT 'FAIT_EMBOUTEILLAGE créée ✅' AS statut;
