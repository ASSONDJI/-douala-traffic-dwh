# Branche `feat/airflow-orchestration`

> **Membre 2** — Orchestration du pipeline ETL avec Apache Airflow

---

## Ce qui a été réalisé

### Fichier principal
```
airflow/dags/dwh_douala_dag.py
```

DAG Airflow complet qui automatise l'intégralité du pipeline ETL du Data Warehouse.

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

---

## Tâches du DAG

| task_id | Script / Fonction | Description |
|---------|-------------------|-------------|
| `extract_osm` | `01_extract_osm_douala.py` | Télécharge le réseau OSM de Douala |
| `extract_meteo` | `02_extract_meteo_douala.py` | Récupère la météo 2022-2024 via Open-Meteo |
| `generate_trafic` | `03_generate_trafic_data.py` | Génère ~2.5M mesures de trafic |
| `load_dim_temps` | Python inline | Charge ~26 280 entrées temporelles |
| `load_dim_lieu` | Python inline | Charge les segments OSM avec géo-enrichissement |
| `load_fait_embouteillage` | Python inline | Charge ~2.5M faits avec résolution FK Kimball |
| `refresh_vues_olap` | Python inline | Rafraîchit les 4 vues matérialisées datamart |

---

## Configuration

### Connexion Airflow requise
La connexion `douala_dwh` est définie automatiquement via la variable d'environnement dans `docker-compose.yml` :

```yaml
AIRFLOW_CONN_DOUALA_DWH: postgresql+psycopg2://dwh_admin:Douala2024!@postgres-dwh/douala_traffic_dwh
```

### Planning
```
schedule_interval = "0 5 * * *"   # 05h00 UTC = 06h00 WAT (heure de Douala)
```

---

## Démarrage

```bash
# 1. Cloner et se placer sur la branche
git clone https://github.com/ASSONDJI/-douala-traffic-dwh.git
cd douala-traffic-dwh
git checkout feat/airflow-orchestration

# 2. Lancer l'infrastructure
cd docker
docker compose up -d

# 3. Attendre que les services soient prêts (~2 min)
docker ps

# 4. Accéder à Airflow
# → http://localhost:8080  (admin / admin)
# → Chercher le DAG : "dwh_douala_pipeline"
# → Activer le toggle et cliquer "Trigger DAG" pour un run manuel
```

---

## Validation du DAG

Le DAG a été validé syntaxiquement :
```bash
python -c "import ast; ast.parse(open('airflow/dags/dwh_douala_dag.py').read()); print('OK')"
# → SYNTAXE OK
```

Toutes les 7 tâches requises sont présentes :
- `extract_osm` ✓
- `extract_meteo` ✓
- `generate_trafic` ✓
- `load_dim_temps` ✓
- `load_dim_lieu` ✓
- `load_fait_embouteillage` ✓
- `refresh_vues_olap` ✓
