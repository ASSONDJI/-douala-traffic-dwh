-- Agrégat : résumé par axe routier
SELECT
    l.axe_principal,
    l.quartier,
    l.arrondissement,
    l.type_route,
    COUNT(*)                                        AS nb_mesures,
    ROUND(AVG(f.indice_congestion)::numeric, 3)     AS congestion_moyenne,
    ROUND(MAX(f.indice_congestion)::numeric, 3)     AS congestion_max,
    ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1)   AS vitesse_moyenne,
    ROUND(AVG(f.delai_supplementaire_min)::numeric, 2) AS delai_moyen_min,
    SUM(f.volume_vehicules)                         AS volume_total,
    SUM(CASE WHEN f.flag_incident THEN 1 ELSE 0 END) AS nb_incidents,
    ROUND(100.0 * SUM(CASE WHEN f.niveau_service IN ('E','F')
          THEN 1 ELSE 0 END) / COUNT(*), 2)         AS pct_temps_sature
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_lieu l ON f.id_lieu = l.id_lieu
WHERE l.est_actif = TRUE
GROUP BY l.axe_principal, l.quartier, l.arrondissement, l.type_route
