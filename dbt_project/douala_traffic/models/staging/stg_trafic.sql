-- Couche staging : nettoyage et standardisation des données brutes
SELECT
    f.id_fait,
    f.id_temps,
    f.id_lieu,
    f.id_vehicule,
    f.id_evenement,
    f.id_capteur,
    f.volume_vehicules,
    f.vitesse_moyenne_kmh,
    f.vitesse_libre_kmh,
    f.indice_congestion,
    f.niveau_service,
    f.delai_supplementaire_min,
    f.longueur_bouchon_km,
    f.flag_incident,
    f.ts
FROM warehouse.fait_embouteillage f
WHERE f.indice_congestion > 0
  AND f.vitesse_moyenne_kmh >= 0
  AND f.volume_vehicules >= 0
