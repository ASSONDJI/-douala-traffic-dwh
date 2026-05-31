-- ============================================================
--  REQUÊTES SQL-OLAP — Entrepôt Embouteillages Douala
--  Méthodologie Kimball — Opérations sur cube de données
--  Grain de base : 1 mesure par segment, par 5 minutes
-- ============================================================


-- ============================================================
--  REQUÊTE 1 — ROLL-UP TEMPOREL
--  Agrégation : 5min → heure → jour → mois → année
-- ============================================================
SELECT
    t.annee, t.mois, t.jour_mois, t.heure, t.minute,
    GROUPING(t.annee, t.mois, t.jour_mois, t.heure, t.minute) AS niveau,
    COUNT(*)                                            AS nb_mesures,
    ROUND(AVG(f.indice_congestion)::numeric, 3)         AS congestion_moyenne,
    ROUND(MIN(f.vitesse_moyenne_kmh)::numeric, 1)       AS vitesse_min_kmh,
    ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1)       AS vitesse_moy_kmh,
    ROUND(MAX(f.indice_congestion)::numeric, 3)         AS congestion_max,
    SUM(f.volume_vehicules)                             AS volume_total,
    ROUND(AVG(f.delai_supplementaire_min)::numeric, 2)  AS delai_moy_min
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_temps t ON f.id_temps = t.id_temps
GROUP BY ROLLUP(t.annee, t.mois, t.jour_mois, t.heure, t.minute)
FETCH FIRST 100 ROWS ONLY;


-- ============================================================
--  REQUÊTE 2 — DRILL-DOWN GÉOGRAPHIQUE
--  Ville → Arrondissement → Quartier → Axe → Segment
-- ============================================================
SELECT * FROM (
    SELECT
        'Douala' AS ville,
        l.arrondissement,
        l.quartier,
        l.axe_principal,
        l.nom_segment,
        CASE
            WHEN GROUPING(l.arrondissement) = 1 THEN 'Niveau VILLE'
            WHEN GROUPING(l.quartier)       = 1 THEN 'Niveau ARRONDISSEMENT'
            WHEN GROUPING(l.axe_principal)  = 1 THEN 'Niveau QUARTIER'
            WHEN GROUPING(l.nom_segment)    = 1 THEN 'Niveau AXE'
            ELSE                                     'Niveau SEGMENT'
        END AS niveau_drill,
        COUNT(*)                                            AS nb_mesures,
        ROUND(AVG(f.indice_congestion)::numeric, 3)         AS congestion_moyenne,
        ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1)       AS vitesse_moy_kmh,
        ROUND(AVG(f.delai_supplementaire_min)::numeric, 2)  AS delai_moy_min,
        SUM(f.volume_vehicules)                             AS volume_total,
        SUM(CASE WHEN f.niveau_service IN ('E','F')
                 THEN 1 ELSE 0 END)                         AS heures_saturees
    FROM warehouse.fait_embouteillage f
    JOIN warehouse.dim_lieu l ON f.id_lieu = l.id_lieu
    GROUP BY ROLLUP(l.arrondissement, l.quartier, l.axe_principal, l.nom_segment)
) sub
ORDER BY arrondissement NULLS LAST, quartier NULLS LAST,
         axe_principal NULLS LAST, congestion_moyenne DESC
FETCH FIRST 50 ROWS ONLY;


-- ============================================================
--  REQUÊTE 3 — SLICE MÉTÉO
--  Filtre sur 1 dimension : heures de pluie uniquement
-- ============================================================
SELECT
    e.sous_type                                         AS condition_meteo,
    e.impact_trafic,
    t.tranche_horaire,
    t.est_weekend,
    COUNT(*)                                            AS nb_mesures,
    ROUND(AVG(f.indice_congestion)::numeric, 3)         AS congestion_moyenne,
    ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1)       AS vitesse_moy_kmh,
    ROUND(AVG(f.delai_supplementaire_min)::numeric, 2)  AS delai_moy_min,
    ROUND(AVG(f.longueur_bouchon_km)::numeric, 3)       AS longueur_bouchon_moy,
    SUM(f.volume_vehicules)                             AS volume_total
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_evenement e ON f.id_evenement = e.id_evenement
JOIN warehouse.dim_temps     t ON f.id_temps     = t.id_temps
WHERE e.type_evenement = 'METEO'
  AND e.sous_type IN ('Pluie legere', 'Pluie forte', 'Orage')
GROUP BY e.sous_type, e.impact_trafic, t.tranche_horaire, t.est_weekend
ORDER BY congestion_moyenne DESC;


-- ============================================================
--  REQUÊTE 4 — DICE MULTI-CRITÈRES
--  Vendredi + Pluie + Axes critiques
-- ============================================================
SELECT
    t.nom_jour, t.tranche_horaire,
    e.sous_type                                         AS condition_meteo,
    l.quartier, l.axe_principal,
    COUNT(*)                                            AS nb_mesures,
    ROUND(AVG(f.indice_congestion)::numeric, 3)         AS congestion_moyenne,
    ROUND(MAX(f.indice_congestion)::numeric, 3)         AS congestion_max,
    ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1)       AS vitesse_moy_kmh,
    ROUND(AVG(f.delai_supplementaire_min)::numeric, 2)  AS delai_moy_min,
    SUM(f.volume_vehicules)                             AS nb_vehicules_total,
    SUM(CASE WHEN f.flag_incident THEN 1 ELSE 0 END)   AS nb_incidents
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_temps     t ON f.id_temps     = t.id_temps
JOIN warehouse.dim_evenement e ON f.id_evenement = e.id_evenement
JOIN warehouse.dim_lieu      l ON f.id_lieu      = l.id_lieu
WHERE t.jour_semaine = 4
  AND e.type_evenement = 'METEO'
  AND e.sous_type IN ('Pluie legere', 'Pluie forte', 'Orage')
  AND l.est_axe_critique = TRUE
GROUP BY t.nom_jour, t.tranche_horaire, e.sous_type, l.quartier, l.axe_principal
ORDER BY congestion_moyenne DESC
FETCH FIRST 20 ROWS ONLY;


-- ============================================================
--  REQUÊTE 5 — PIVOT CUBE — Heatmap Jour x Heure
-- ============================================================
SELECT * FROM (
    SELECT
        t.nom_jour, t.jour_semaine, t.heure,
        e.sous_type AS condition_meteo,
        CASE
            WHEN GROUPING(t.nom_jour) = 1
             AND GROUPING(t.heure) = 1
             AND GROUPING(e.sous_type) = 1 THEN 'TOTAL GLOBAL'
            WHEN GROUPING(t.heure) = 1
             AND GROUPING(e.sous_type) = 1 THEN 'Total par JOUR'
            WHEN GROUPING(t.nom_jour) = 1
             AND GROUPING(e.sous_type) = 1 THEN 'Total par HEURE'
            WHEN GROUPING(e.sous_type) = 1 THEN 'Jour x Heure'
            ELSE                                'Jour x Heure x Meteo'
        END AS dimension_active,
        COUNT(*)                                            AS nb_mesures,
        ROUND(AVG(f.indice_congestion)::numeric, 3)         AS congestion_moyenne,
        ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1)       AS vitesse_moy_kmh,
        SUM(f.volume_vehicules)                             AS volume_total
    FROM warehouse.fait_embouteillage f
    JOIN warehouse.dim_temps     t ON f.id_temps     = t.id_temps
    JOIN warehouse.dim_evenement e ON f.id_evenement = e.id_evenement
    GROUP BY CUBE(t.nom_jour, t.jour_semaine, t.heure, e.sous_type)
) sub
WHERE dimension_active = 'Jour x Heure'
ORDER BY jour_semaine NULLS LAST, heure NULLS LAST
FETCH FIRST 50 ROWS ONLY;


-- ============================================================
--  REQUÊTE 6 — RANKING + LAG (variation mensuelle)
-- ============================================================
WITH congestion_mensuelle AS (
    SELECT
        t.annee, t.mois, t.nom_mois,
        l.quartier, l.axe_principal,
        COUNT(*)                                        AS nb_mesures,
        ROUND(AVG(f.indice_congestion)::numeric, 3)     AS congestion_moy,
        ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1)   AS vitesse_moy,
        SUM(f.volume_vehicules)                         AS volume_total
    FROM warehouse.fait_embouteillage f
    JOIN warehouse.dim_temps t ON f.id_temps = t.id_temps
    JOIN warehouse.dim_lieu  l ON f.id_lieu  = l.id_lieu
    GROUP BY t.annee, t.mois, t.nom_mois, l.quartier, l.axe_principal
)
SELECT
    annee, mois, nom_mois, quartier, axe_principal,
    congestion_moy, vitesse_moy, volume_total,
    RANK() OVER (
        PARTITION BY annee, mois
        ORDER BY congestion_moy DESC
    ) AS rang_du_mois,
    LAG(congestion_moy, 1) OVER (
        PARTITION BY quartier, axe_principal
        ORDER BY annee, mois
    ) AS congestion_mois_precedent,
    ROUND((congestion_moy - LAG(congestion_moy, 1) OVER (
        PARTITION BY quartier, axe_principal
        ORDER BY annee, mois
    ))::numeric, 3) AS variation,
    CASE
        WHEN congestion_moy > LAG(congestion_moy, 1) OVER (
            PARTITION BY quartier, axe_principal
            ORDER BY annee, mois
        ) THEN 'DETERIORATION'
        WHEN congestion_moy < LAG(congestion_moy, 1) OVER (
            PARTITION BY quartier, axe_principal
            ORDER BY annee, mois
        ) THEN 'AMELIORATION'
        ELSE 'STABLE'
    END AS tendance
FROM congestion_mensuelle
ORDER BY annee, mois, rang_du_mois
FETCH FIRST 50 ROWS ONLY;
