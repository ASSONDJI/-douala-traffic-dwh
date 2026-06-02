-- Table de faits enrichie avec jointures dimensions
SELECT
    f.id_fait,
    f.ts,
    t.date_complete,
    t.nom_jour,
    t.heure,
    t.tranche_horaire,
    t.est_heure_pointe,
    t.est_weekend,
    t.saison_cameroun,
    l.nom_segment,
    l.quartier,
    l.arrondissement,
    l.axe_principal,
    l.type_route,
    l.est_axe_critique,
    e.sous_type         AS condition_meteo,
    e.impact_trafic,
    f.volume_vehicules,
    f.vitesse_moyenne_kmh,
    f.vitesse_libre_kmh,
    f.indice_congestion,
    f.niveau_service,
    f.delai_supplementaire_min,
    f.longueur_bouchon_km,
    f.flag_incident,
    CASE
        WHEN f.indice_congestion >= 4.0 THEN 'Bloqué'
        WHEN f.indice_congestion >= 2.5 THEN 'Saturé'
        WHEN f.indice_congestion >= 2.0 THEN 'Instable'
        WHEN f.indice_congestion >= 1.43 THEN 'Chargé'
        WHEN f.indice_congestion >= 1.11 THEN 'Bon'
        ELSE                                  'Fluide'
    END AS libelle_congestion
FROM warehouse.fait_embouteillage f
JOIN warehouse.dim_temps     t ON f.id_temps     = t.id_temps
JOIN warehouse.dim_lieu      l ON f.id_lieu      = l.id_lieu
JOIN warehouse.dim_evenement e ON f.id_evenement = e.id_evenement
WHERE l.est_actif = TRUE
