-- Dimension temps avec indicateurs analytiques enrichis
SELECT
    id_temps,
    date_complete,
    date_heure,
    annee,
    trimestre,
    mois,
    nom_mois,
    jour_mois,
    jour_semaine,
    nom_jour,
    heure,
    minute,
    est_weekend,
    est_jour_ferie_cm,
    nom_jour_ferie,
    tranche_horaire,
    est_heure_pointe,
    saison_cameroun,
    CASE
        WHEN est_heure_pointe AND NOT est_weekend THEN 'Pointe semaine'
        WHEN est_heure_pointe AND est_weekend     THEN 'Pointe weekend'
        WHEN est_weekend                          THEN 'Weekend creux'
        ELSE                                           'Semaine creuse'
    END AS categorie_temporelle
FROM warehouse.dim_temps
