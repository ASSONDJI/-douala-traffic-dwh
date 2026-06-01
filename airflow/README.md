# Branche `feat/airflow-orchestration`

> **Membre 2** — Orchestration du pipeline ETL avec Apache Airflow

---

## Objectif

Créer le DAG Apache Airflow qui automatise l'intégralité du pipeline ETL
du Data Warehouse Embouteillages Douala, de l'extraction des données brutes
jusqu'au rafraîchissement des vues OLAP pour les dashboards Superset.

---

## Fichiers ajoutés

```
airflow/
├── dags/
│   └── dwh_douala_dag.py   ← DAG principal (ce fichier)
├── plugins/                 (vide — prévu pour extensions futures)
└── README.md               ← cette documentation
```

---

## Architecture du pipeline

```
debut_pipeline
     │
┌────┴────┐
│         │
extract   extract          ← Parallèles (indépendants)
osm       meteo
│         │
└────┬────┘
     │
generate_trafic            ← Dépend des deux extractions
     │
┌────┴────┐
│         │
load      load             ← Parallèles (indépendants)
dim_temps dim_lieu
│         │
└────┬────┘
     │
load_fait_embouteillage    ← Dépend de toutes les dimensions
     │
refresh_vues_olap          ← Met à jour les 4 vues datamart
     │
fin_pipeline
```

Le graphe est optimisé :
- `extract_osm` et `extract_meteo` tournent **en parallèle** (indépendants)
- `load_dim_temps` et `load_dim_lieu` tournent **en parallèle** (indépendants)
- `load_fait_embouteillage` attend que **toutes les dimensions** soient chargées
  avant d'insérer les faits (résolution FK Kimball)

---

## Tâches du DAG

| task_id | Script appelé | Description |
|---------|---------------|-------------|
| `extract_osm` | `etl/extract/01_extract_osm_douala.py` | Télécharge le réseau routier de Douala via OpenStreetMap (68 058 segments) |
| `extract_meteo` | `etl/extract/02_extract_meteo_douala.py` | Récupère les données météo 2022-2024 via Open-Meteo API |
| `generate_trafic` | `etl/extract/03_generate_trafic_data.py` | Génère ~2.5M mesures de trafic (20 axes × 2 ans × 5 min) |
| `load_dim_temps` | `etl/load/01_load_dim_temps.py` | Charge DIM_TEMPS — grain 5 min, ~526 000 entrées 2022-2026 |
| `load_dim_lieu` | `etl/load/02_load_dim_lieu.py` | Charge DIM_LIEU — 68 058 segments OSM avec géo-enrichissement |
| `load_fait_embouteillage` | `etl/load/03_load_fait_embouteillage.py` | Charge ~2.5M faits avec résolution des 6 FK Kimball |
| `refresh_vues_olap` | Fonction Python inline | Rafraîchit les 4 vues matérialisées du datamart |

---

## Détails techniques

### Connexion PostgreSQL
La connexion `douala_dwh` est définie automatiquement dans `docker-compose.yml`
via la variable `AIRFLOW_CONN_DOUALA_DWH`. Aucune configuration manuelle
dans l'interface Airflow n'est nécessaire.

> ⚠️ **Limitation connue (projet académique)** : les identifiants de connexion
> sont définis en clair dans `docker-compose.yml`. En production, utiliser
> des secrets Airflow ou un gestionnaire de secrets (Vault, AWS Secrets Manager).

### Planning
```
schedule_interval = "0 5 * * *"   # 05h00 UTC = 06h00 WAT (heure de Douala)
```
Exécution automatique **tous les jours à 06h00** (avant les heures de pointe).

### Idempotence
Toutes les insertions utilisent `ON CONFLICT DO NOTHING` — le DAG peut être
relancé sans créer de doublons.

### Compatibilité Docker
Le DAG passe automatiquement `PGHOST=postgres-dwh` aux scripts `etl/load/`
via les variables d'environnement — les scripts fonctionnent aussi bien
en local (`localhost`) qu'en Docker (`postgres-dwh`).

### Création automatique des dossiers
Les dossiers `data/raw/osm`, `data/raw/meteo` et `data/generated` sont
créés automatiquement au démarrage du DAG (`os.makedirs(..., exist_ok=True`)
pour éviter les `PermissionError`.

---

## Démarrage rapide

```bash
# 1. Cloner et se placer sur la branche
git clone https://github.com/ASSONDJI/-douala-traffic-dwh.git
cd douala-traffic-dwh
git checkout feat/airflow-orchestration

# 2. Lancer l'infrastructure (Docker Desktop doit être ouvert)
cd docker
docker compose up -d

# 3. Attendre ~5 min (installation des packages osmnx, geopandas...)
docker logs douala_airflow_scheduler --follow
# → Attendre "Successfully installed osmnx..." puis "Scheduler started"

# 4. Accéder à Airflow
# → http://localhost:8080  (admin / admin)
# → Chercher le DAG : "dwh_douala_pipeline"
# → Activer le toggle et cliquer "Trigger DAG ▶" pour un run manuel
```

---

## Validation

### Syntaxe Python
```bash
python -c "import ast; ast.parse(open('airflow/dags/dwh_douala_dag.py', encoding='utf-8').read()); print('OK')"
# → Syntaxe OK
```

### Tâches présentes (9 au total)
| Tâche | Statut |
|-------|--------|
| `debut_pipeline` | ✅ |
| `extract_osm` | ✅ |
| `extract_meteo` | ✅ |
| `generate_trafic` | ✅ |
| `load_dim_temps` | ✅ |
| `load_dim_lieu` | ✅ |
| `load_fait_embouteillage` | ✅ |
| `refresh_vues_olap` | ✅ |
| `fin_pipeline` | ✅ |

### Résultats des tests (review chef)
| Test | Résultat |
|------|----------|
| Syntaxe Python | ✅ Valide |
| DAG visible dans Airflow UI | ✅ `dwh_douala_pipeline` |
| `debut_pipeline` | ✅ SUCCESS |
| `extract_meteo` | ✅ API répond correctement |
| Architecture parallèle | ✅ Validée |
| PermissionError `data/raw/meteo` | ✅ Corrigé (makedirs) |

---

## Perspectives d'évolution

- Remplacer `_PIP_ADDITIONAL_REQUIREMENTS` par une image Docker personnalisée
- Utiliser les secrets Airflow pour les identifiants PostgreSQL
- Ajouter des alertes email en cas d'échec du pipeline
- Intégrer des tests de qualité des données (Great Expectations)
