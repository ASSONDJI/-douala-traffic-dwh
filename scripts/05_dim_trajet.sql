-- ============================================================
--  DIM_TRAJET — Dimension Trajet (Origine → Destination)
--  Type SCD : 2 (historique si itinéraire change)
--  Grain : 1 paire Origine-Destination dans Douala
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_trajet (
    id_trajet               SERIAL      PRIMARY KEY,
    
    code_trajet             VARCHAR(50) NOT NULL,
    -- Format : 'OD_AKWA_NDOKOTI', 'OD_BONABERI_BASSA'

    -- Origine
    quartier_origine        VARCHAR(100) NOT NULL,
    arrondissement_origine  VARCHAR(100) NOT NULL,
    
    -- Destination
    quartier_destination    VARCHAR(100) NOT NULL,
    arrondissement_destination VARCHAR(100) NOT NULL,

    -- Caractéristiques du trajet
    distance_km             DECIMAL(8,3) NOT NULL,
    duree_reference_min     DECIMAL(8,2) NOT NULL,
    -- Durée sans congestion (vitesse libre)

    nombre_segments         SMALLINT    NOT NULL DEFAULT 1,
    -- Nombre de segments de route composant ce trajet
    
    est_trajet_principal    BOOLEAN     NOT NULL DEFAULT FALSE,
    -- TRUE pour les grands axes : Centre → Bonabéri, Akwa → Ndokoti...
    
    description_trajet      VARCHAR(300),

    -- SCD Type 2
    date_debut_validite     DATE        NOT NULL DEFAULT CURRENT_DATE,
    date_fin_validite       DATE,
    est_actif               BOOLEAN     NOT NULL DEFAULT TRUE,
    version                 SMALLINT    NOT NULL DEFAULT 1,

    date_chargement         TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_trajet_code    ON warehouse.dim_trajet(code_trajet);
CREATE INDEX IF NOT EXISTS idx_dim_trajet_actif   ON warehouse.dim_trajet(est_actif);
CREATE INDEX IF NOT EXISTS idx_dim_trajet_principal ON warehouse.dim_trajet(est_trajet_principal);

COMMENT ON TABLE warehouse.dim_trajet IS
'Dimension trajet Origine-Destination à Douala.
SCD Type 2 : permet de tracer l''évolution des durées de référence
si les infrastructures routières changent.';

SELECT 'DIM_TRAJET créée ✅' AS statut;
