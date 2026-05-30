--  VUES DATAMART — Opérations OLAP pré-calculées
--  Ces vues matérialisées servent les dashboards Superset
--  et démontrent les opérations OLAP (cours Annaba séance 6-7)


-- ── Vue 1 : Roll-up Horaire ────────────────────────────────
-- Agrège les mesures de 5 min → synthèse par heure
CREATE MATERIALIZED VIEW IF NOT EXISTS datamart.vm_trafic_horaire AS
SELECT
    t.date_complete,
    t.annee,
    t.mois,
    t.nom_mois,
    t.jour_semaine,
    t.nom_jour,
    t.heure,
    t.tranche_horaire,
    t.est_heure_pointe,
    t.est_weekend,
    l.quartier,
    l.axe_principal,
    l.arrondissement,
    l.est_axe_critique,
    COUNT(*)                                AS nb_mesures,
    AVG(f.vitesse_moyenne_kmh)              AS vitesse_moy_kmh,
    AVG(f.indice_congestion)                AS indice_cong_moy,
    MAX(f.indice_congestion)                AS indice_cong_max,
    SUM(f.volume_vehicules)                 AS volume_total,
    AVG(f.longueur_bouchon_km)              AS longueur_bouchon_moy,
    AVG(f.delai_supplementaire_min)         AS delai_moy_min,
    -- Mode du niveau de service (le plus fréquent sur l'heure)
    MODE() WITHIN GROUP (ORDER BY f.niveau_service) AS niveau_service_dominant,
    SUM(CASE WHEN f.flag_incident THEN 1 ELSE 0 END) AS nb_incidents
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_temps t  ON f.id_temps = t.id_temps
JOIN warehouse.dim_lieu  l  ON f.id_lieu  = l.id_lieu
WHERE l.est_actif = TRUE
GROUP BY
    t.date_complete, t.annee, t.mois, t.nom_mois,
    t.jour_semaine, t.nom_jour, t.heure, t.tranche_horaire,
    t.est_heure_pointe, t.est_weekend,
    l.quartier, l.axe_principal, l.arrondissement, l.est_axe_critique
WITH DATA;

-- ── Vue 2 : Axes les plus congestionnés ───────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS datamart.vm_axes_critiques AS
SELECT
    l.axe_principal,
    l.quartier,
    l.arrondissement,
    COUNT(*)                            AS nb_observations,
    AVG(f.indice_congestion)            AS indice_cong_moyen,
    AVG(f.vitesse_moyenne_kmh)          AS vitesse_moyenne,
    SUM(f.delai_supplementaire_min)     AS delai_total_cumule_min,
    AVG(f.longueur_bouchon_km)          AS longueur_bouchon_moy,
    SUM(CASE WHEN f.niveau_service = 'F' THEN 1 ELSE 0 END) AS heures_bloquees,
    ROUND(100.0 * SUM(CASE WHEN f.niveau_service IN ('E','F')
          THEN 1 ELSE 0 END) / COUNT(*), 2)    AS pct_temps_sature
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_lieu l ON f.id_lieu = l.id_lieu
WHERE l.est_actif = TRUE
GROUP BY l.axe_principal, l.quartier, l.arrondissement
ORDER BY indice_cong_moyen DESC
WITH DATA;

-- ── Vue 3 : Impact météo (Slice sur type_evenement = 'METEO') ──
CREATE MATERIALIZED VIEW IF NOT EXISTS datamart.vm_impact_meteo AS
SELECT
    e.sous_type                         AS condition_meteo,
    e.impact_trafic,
    e.coefficient_impact,
    COUNT(*)                            AS nb_observations,
    AVG(f.indice_congestion)            AS indice_cong_moyen,
    AVG(f.vitesse_moyenne_kmh)          AS vitesse_moy,
    AVG(f.delai_supplementaire_min)     AS delai_moy_min,
    AVG(f.longueur_bouchon_km)          AS longueur_bouchon_moy
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_evenement e ON f.id_evenement = e.id_evenement
WHERE e.type_evenement = 'METEO'
GROUP BY e.sous_type, e.impact_trafic, e.coefficient_impact
ORDER BY indice_cong_moyen DESC
WITH DATA;

-- ── Vue 4 : Profil semaine (pour heatmap) ─────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS datamart.vm_profil_semaine AS
SELECT
    t.nom_jour,
    t.jour_semaine,
    t.heure,
    AVG(f.indice_congestion)            AS indice_cong_moyen,
    AVG(f.vitesse_moyenne_kmh)          AS vitesse_moy,
    SUM(f.volume_vehicules)             AS volume_total,
    COUNT(*)                            AS nb_mesures
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_temps t ON f.id_temps = t.id_temps
GROUP BY t.nom_jour, t.jour_semaine, t.heure
ORDER BY t.jour_semaine, t.heure
WITH DATA;

-- Index sur les vues matérialisées
CREATE INDEX IF NOT EXISTS idx_vm_horaire_date
    ON datamart.vm_trafic_horaire(date_complete);
CREATE INDEX IF NOT EXISTS idx_vm_horaire_quartier
    ON datamart.vm_trafic_horaire(quartier);
CREATE INDEX IF NOT EXISTS idx_vm_axes_nom
    ON datamart.vm_axes_critiques(axe_principal);

SELECT 'Vues OLAP datamart créées ' AS statut;
