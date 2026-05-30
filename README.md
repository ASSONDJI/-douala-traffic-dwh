# 🚦 Entrepôt de Données — Embouteillages Douala

> Projet Master 1 IA — Méthodologie Kimball  
> Ville : Douala, Cameroun

## Stack technique
- **BDD** : PostgreSQL 16
- **ETL** : Apache Airflow 2.8 + Python
- **Transformations** : dbt Core
- **Dashboards** : Apache Superset 3.1
- **Infra** : Docker Compose

## Démarrage rapide

```bash
cd docker
docker compose up -d
```

| Service    | URL                    | Login        |
|------------|------------------------|--------------|
| Airflow    | http://localhost:8080  | admin/admin  |
| Superset   | http://localhost:8088  | admin/admin  |
| PostgreSQL | localhost:5432         | dwh_admin/Douala2024! |

## Modèle dimensionnel (Kimball)

**3 Tables de faits :**
- `FAIT_MESURE_TRAFIC` — Transaction (mesure capteur toutes les 5 min)
- `FAIT_EMBOUTEILLAGE` — Accumulating Snapshot (cycle de vie d'un bouchon)
- `FAIT_SNAPSHOT_HORAIRE` — Periodic Snapshot (état horaire par segment)

**6 Dimensions conformées :**
`DIM_TEMPS` · `DIM_LIEU` · `DIM_VEHICULE` · `DIM_EVENEMENT` · `DIM_TRAJET` · `DIM_CAPTEUR`

## Équipe

 **Membre  et Rôle :**
 **Assondji Malaika :**  Chef de projet, Architecture, ETL, gestion global et supervisation
 **Soh Duclair :**  Modèle physique SQL 
 **Talla Donald & Dagheng Patricia :** Collecte données & génération 
 **Wati Beldouce :**  Dashboards Superset 
