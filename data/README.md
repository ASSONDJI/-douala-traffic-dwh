# Datasets — Entrepôt de Données Embouteillages Douala

## Données disponibles

### sample_trafic_10k.csv
Échantillon représentatif de 10 000 mesures de trafic.

| Colonne | Type | Description |
|---------|------|-------------|
| date_heure | TIMESTAMP | Horodatage (grain 5 minutes) |
| code_segment | STRING | Identifiant OSM du segment |
| nom_segment | STRING | Nom de l'axe routier |
| type_route | STRING | Voie rapide / Avenue principale / Rue secondaire |
| condition_meteo | STRING | Ensoleille / Pluie legere / Pluie forte / Orage |
| volume_vehicules | INT | Nombre de véhicules comptés |
| vitesse_moyenne_kmh | FLOAT | Vitesse moyenne observée (km/h) |
| vitesse_libre_kmh | FLOAT | Vitesse de référence sans congestion |
| indice_congestion | FLOAT | vitesse_libre ÷ vitesse_moyenne (1.0 = fluide) |
| niveau_service | CHAR | LOS A (fluide) → F (bloqué) |
| delai_supplementaire_min | FLOAT | Minutes perdues à cause du bouchon |
| lat_centre | FLOAT | Latitude GPS du segment |
| lon_centre | FLOAT | Longitude GPS du segment |

### meteo_douala_2022_2024.csv
Données météo horaires réelles — Douala 2022-2024.
Source : Open-Meteo API (gratuite, sans clé API)
26 304 enregistrements horaires.

### axes_critiques_douala.csv
359 axes critiques de Douala avec coordonnées GPS réelles.
Source : OpenStreetMap (licence ODbL)

## Régénérer le dataset complet (4 210 560 lignes — 791 MB)

```bash
source venv/bin/activate
python3 etl/extract/01_extract_osm_douala.py
python3 etl/extract/02_extract_meteo_douala.py
python3 etl/extract/03_generate_trafic_data.py
```

## Sources

| Source | Données | Licence |
|--------|---------|---------|
| OpenStreetMap | Réseau routier Douala réel | ODbL |
| Open-Meteo API | Météo historique 2022-2024 | CC BY 4.0 |
| Simulation Python | Trafic généré (patterns réels) | MIT |

## Statistiques du dataset complet

| Métrique | Valeur |
|----------|--------|
| Total mesures | 2 502 240 |
| Période | 2023-01-01 → 2024-12-31 |
| Grain | 5 minutes |
| Axes couverts | 20 axes critiques |
| Véhicules comptés | 41 684 959 |
| Incidents détectés | 5 037 |
| Indice congestion moyen | 1.249 (LOS B) |
