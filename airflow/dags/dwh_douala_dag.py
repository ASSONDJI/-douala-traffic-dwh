"""
╔══════════════════════════════════════════════════════════════════╗
║     DAG — Entrepôt de Données Embouteillages Douala             ║
║     Pipeline ETL complet — Méthodologie Kimball                  ║
║                                                                  ║
║     Auteur  : Membre 2 — feat/airflow-orchestration             ║
║     Projet  : Master 1 IA — DWH Douala Traffic                  ║
║     Version : 3.0.0  (aligné sur etl/load/ du chef)            ║
╚══════════════════════════════════════════════════════════════════╝

Graphe d'exécution :

  debut_pipeline
       │
  ┌────┴────┐
  │         │
extract   extract        ← parallèles
 osm       meteo
  │         │
  └────┬────┘
       │
  generate_trafic
       │
  ┌────┴────┐
  │         │
load      load           ← parallèles
dim_temps dim_lieu
  │         │
  └────┬────┘
       │
  load_fait_embouteillage
       │
  refresh_vues_olap
       │
  fin_pipeline

Scripts de référence :
  - etl/extract/01_extract_osm_douala.py
  - etl/extract/02_extract_meteo_douala.py
  - etl/extract/03_generate_trafic_data.py
  - etl/load/01_load_dim_temps.py      ← script du chef
  - etl/load/02_load_dim_lieu.py       ← script du chef
  - etl/load/03_load_fait_embouteillage.py ← script du chef

Planning : tous les jours à 06h00 WAT (UTC+1 → cron: 0 5 * * *)
Connexion : AIRFLOW_CONN_DOUALA_DWH (définie dans docker-compose.yml)
"""

from __future__ import annotations

import os
import logging
import subprocess
import sys
from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago

# ──────────────────────────────────────────────────────────────────
#  Configuration globale
# ──────────────────────────────────────────────────────────────────

CONN_ID  = "douala_dwh"
DAG_ID   = "dwh_douala_pipeline"

# Chemins montés dans le conteneur (volumes docker-compose.yml)
ETL_EXTRACT = "/opt/airflow/etl/extract"
ETL_LOAD    = "/opt/airflow/etl/load"
DATA_DIR    = "/opt/airflow/data"

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
#  Fonction utilitaire — exécution d'un script Python
# ──────────────────────────────────────────────────────────────────

def run_script(script_path: str, label: str):
    """
    Lance un script Python et lève une exception si il échoue.

    Surcharge PGHOST=postgres-dwh pour que les scripts etl/load/
    du chef (qui utilisent host='localhost') se connectent au bon
    conteneur PostgreSQL dans le réseau Docker.
    """
    if not os.path.exists(script_path):
        raise FileNotFoundError(
            f"Script introuvable : {script_path}\n"
            "Vérifiez les volumes dans docker-compose.yml"
        )

    # Environnement avec le bon host Docker pour PostgreSQL
    env = os.environ.copy()
    env["PGHOST"]     = "postgres-dwh"   # host Docker (pas localhost)
    env["PGPORT"]     = "5432"
    env["PGDATABASE"] = "douala_traffic_dwh"
    env["PGUSER"]     = "dwh_admin"
    env["PGPASSWORD"] = "Douala2024!"

    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        cwd="/opt/airflow",
        env=env,
    )
    if result.stdout:
        log.info(result.stdout)
    if result.returncode != 0:
        log.error(result.stderr)
        raise RuntimeError(f"{label} échoué (code {result.returncode})\n{result.stderr}")
    log.info(f"  ✓ {label} terminé")


# ──────────────────────────────────────────────────────────────────
#  TÂCHE 1 — extract_osm
#  Script : etl/extract/01_extract_osm_douala.py
#  Sortie : data/raw/osm/segments_douala.csv
#           data/raw/osm/axes_critiques_douala.csv
# ──────────────────────────────────────────────────────────────────

def task_extract_osm(**context):
    """
    Extraction du réseau routier de Douala via OpenStreetMap.
    Durée estimée : 3-8 min (appel API OSM).
    """
    log.info("=" * 60)
    log.info("  TÂCHE 1 — Extraction OSM réseau routier Douala")
    log.info("=" * 60)

    run_script(
        os.path.join(ETL_EXTRACT, "01_extract_osm_douala.py"),
        "Extraction OSM"
    )

    # Vérification de la sortie
    out = os.path.join(DATA_DIR, "raw/osm/segments_douala.csv")
    if not os.path.exists(out):
        raise FileNotFoundError(f"Fichier de sortie absent : {out}")


# ──────────────────────────────────────────────────────────────────
#  TÂCHE 2 — extract_meteo
#  Script : etl/extract/02_extract_meteo_douala.py
#  Sortie : data/raw/meteo/meteo_douala_2022_2024.csv
# ──────────────────────────────────────────────────────────────────

def task_extract_meteo(**context):
    """
    Extraction météo historique Douala 2022-2024 via Open-Meteo API.
    Durée estimée : 1-3 min.
    """
    log.info("=" * 60)
    log.info("  TÂCHE 2 — Extraction météo historique Douala")
    log.info("=" * 60)

    run_script(
        os.path.join(ETL_EXTRACT, "02_extract_meteo_douala.py"),
        "Extraction météo"
    )

    out = os.path.join(DATA_DIR, "raw/meteo/meteo_douala_2022_2024.csv")
    if not os.path.exists(out):
        raise FileNotFoundError(f"Fichier de sortie absent : {out}")


# ──────────────────────────────────────────────────────────────────
#  TÂCHE 3 — generate_trafic
#  Script : etl/extract/03_generate_trafic_data.py
#  Entrée : data/raw/osm/axes_critiques_douala.csv
#           data/raw/meteo/meteo_douala_2022_2024.csv
#  Sortie : data/generated/trafic_douala_2023_2024.csv (~2.5M lignes)
# ──────────────────────────────────────────────────────────────────

def task_generate_trafic(**context):
    """
    Génération vectorisée des mesures de trafic 2023-2024.
    Durée estimée : 5-15 min.
    """
    log.info("=" * 60)
    log.info("  TÂCHE 3 — Génération données trafic 2023-2024")
    log.info("=" * 60)

    # Vérification des prérequis (sorties des tâches 1 et 2)
    for f in [
        os.path.join(DATA_DIR, "raw/osm/axes_critiques_douala.csv"),
        os.path.join(DATA_DIR, "raw/meteo/meteo_douala_2022_2024.csv"),
    ]:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Prérequis manquant : {f}")

    run_script(
        os.path.join(ETL_EXTRACT, "03_generate_trafic_data.py"),
        "Génération trafic"
    )

    out = os.path.join(DATA_DIR, "generated/trafic_douala_2023_2024.csv")
    if not os.path.exists(out):
        raise FileNotFoundError(f"Fichier de sortie absent : {out}")


# ──────────────────────────────────────────────────────────────────
#  TÂCHE 4 — load_dim_temps
#  Script : etl/load/01_load_dim_temps.py (créé par le chef)
#
#  Ce script du chef gère :
#  - id_temps = BIGINT format YYYYMMDDHHMM
#  - Grain 5 minutes, période 2022-2026
#  - Jours fériés Cameroun (7 jours officiels)
#  - saison_cameroun, tranche_horaire, est_heure_pointe
#  - ON CONFLICT (id_temps) DO NOTHING
# ──────────────────────────────────────────────────────────────────

def task_load_dim_temps(**context):
    """
    Chargement de warehouse.dim_temps.
    Délègue au script etl/load/01_load_dim_temps.py du chef.
    ~526 000 entrées (5 ans × 365j × 24h × 12 tranches).
    """
    log.info("=" * 60)
    log.info("  TÂCHE 4 — Chargement DIM_TEMPS")
    log.info("=" * 60)

    run_script(
        os.path.join(ETL_LOAD, "01_load_dim_temps.py"),
        "Chargement DIM_TEMPS"
    )


# ──────────────────────────────────────────────────────────────────
#  TÂCHE 5 — load_dim_lieu
#  Script : etl/load/02_load_dim_lieu.py (créé par le chef)
#
#  Ce script du chef gère :
#  - Lecture de data/raw/osm/segments_douala.csv
#  - Colonnes exactes : code_segment, nom_segment, axe_principal,
#    type_route, quartier, arrondissement, commune, region, pays,
#    lat/lon debut/fin/centre, longueur_km, nombre_voies,
#    capacite_vehicules_h, a_feux_circulation, a_rond_point,
#    est_pont, est_axe_critique, zone_type, source_donnee
#  - ON CONFLICT DO NOTHING
# ──────────────────────────────────────────────────────────────────

def task_load_dim_lieu(**context):
    """
    Chargement de warehouse.dim_lieu depuis les données OSM.
    Délègue au script etl/load/02_load_dim_lieu.py du chef.
    ~68 058 segments OSM de Douala.
    """
    log.info("=" * 60)
    log.info("  TÂCHE 5 — Chargement DIM_LIEU")
    log.info("=" * 60)

    # Vérification du prérequis (sortie de extract_osm)
    osm_file = os.path.join(DATA_DIR, "raw/osm/segments_douala.csv")
    if not os.path.exists(osm_file):
        raise FileNotFoundError(f"Prérequis manquant : {osm_file}")

    run_script(
        os.path.join(ETL_LOAD, "02_load_dim_lieu.py"),
        "Chargement DIM_LIEU"
    )


# ──────────────────────────────────────────────────────────────────
#  TÂCHE 6 — load_fait_embouteillage
#  Script : etl/load/03_load_fait_embouteillage.py (créé par le chef)
#
#  Ce script du chef gère :
#  - Lecture de data/generated/trafic_douala_2023_2024.csv
#  - Résolution des 5 FK : id_temps, id_lieu, id_evenement,
#    id_vehicule (INCONNU), id_capteur (SIM_PYTHON)
#  - Mapping météo : 'Ensoleille'→'Ensoleille' (sans accents dans les deux)
#  - Rafraîchissement des 4 vues matérialisées datamart
#  - ON CONFLICT DO NOTHING
# ──────────────────────────────────────────────────────────────────

def task_load_fait_embouteillage(**context):
    """
    Chargement de warehouse.fait_embouteillage.
    Délègue au script etl/load/03_load_fait_embouteillage.py du chef.
    ~2 502 240 faits + refresh vues OLAP inclus dans le script.
    """
    log.info("=" * 60)
    log.info("  TÂCHE 6 — Chargement FAIT_EMBOUTEILLAGE")
    log.info("=" * 60)

    # Vérification du prérequis
    trafic_file = os.path.join(DATA_DIR, "generated/trafic_douala_2023_2024.csv")
    if not os.path.exists(trafic_file):
        raise FileNotFoundError(f"Prérequis manquant : {trafic_file}")

    run_script(
        os.path.join(ETL_LOAD, "03_load_fait_embouteillage.py"),
        "Chargement FAIT_EMBOUTEILLAGE"
    )


# ──────────────────────────────────────────────────────────────────
#  TÂCHE 7 — refresh_vues_olap
#  Note : le script 03_load_fait_embouteillage.py du chef inclut
#  déjà le refresh des vues. Cette tâche permet de les rafraîchir
#  indépendamment (ex: run manuel sans recharger les faits).
# ──────────────────────────────────────────────────────────────────

def task_refresh_vues_olap(**context):
    """
    Rafraîchissement des vues matérialisées du datamart.
    Exécuté après load_fait_embouteillage pour garantir
    que les dashboards Superset sont à jour.
    """
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    log.info("=" * 60)
    log.info("  TÂCHE 7 — Rafraîchissement vues OLAP datamart")
    log.info("=" * 60)

    hook = PostgresHook(postgres_conn_id=CONN_ID)
    conn = hook.get_conn()
    conn.autocommit = True
    cur  = conn.cursor()

    vues = [
        "datamart.vm_trafic_horaire",
        "datamart.vm_axes_critiques",
        "datamart.vm_impact_meteo",
        "datamart.vm_profil_semaine",
    ]

    for vue in vues:
        log.info(f"  Rafraîchissement : {vue} ...")
        try:
            cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {vue}")
            log.info(f"    ✓ {vue} — OK (concurrent)")
        except Exception as e:
            log.warning(f"    Fallback standard ({e})")
            cur.execute(f"REFRESH MATERIALIZED VIEW {vue}")
            log.info(f"    ✓ {vue} — OK (standard)")

    cur.close()
    conn.close()
    log.info("  ✓ Toutes les vues OLAP sont à jour")


# ──────────────────────────────────────────────────────────────────
#  Définition du DAG
# ──────────────────────────────────────────────────────────────────

default_args = {
    "owner"            : "dwh_douala_team",
    "depends_on_past"  : False,
    "email_on_failure" : False,
    "email_on_retry"   : False,
    "retries"          : 2,
    "retry_delay"      : timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

with DAG(
    dag_id=DAG_ID,
    description=(
        "Pipeline ETL complet — Entrepôt Embouteillages Douala. "
        "Orchestre extraction OSM + météo, génération trafic, "
        "chargement Kimball (6 dims + 1 fait) et refresh vues OLAP."
    ),
    default_args=default_args,
    schedule_interval="0 5 * * *",   # 06h00 WAT = 05h00 UTC
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["dwh", "douala", "traffic", "kimball", "etl"],
) as dag:

    debut_pipeline = EmptyOperator(task_id="debut_pipeline")

    t_extract_osm = PythonOperator(
        task_id="extract_osm",
        python_callable=task_extract_osm,
    )

    t_extract_meteo = PythonOperator(
        task_id="extract_meteo",
        python_callable=task_extract_meteo,
    )

    t_generate_trafic = PythonOperator(
        task_id="generate_trafic",
        python_callable=task_generate_trafic,
    )

    t_load_dim_temps = PythonOperator(
        task_id="load_dim_temps",
        python_callable=task_load_dim_temps,
    )

    t_load_dim_lieu = PythonOperator(
        task_id="load_dim_lieu",
        python_callable=task_load_dim_lieu,
    )

    t_load_fait = PythonOperator(
        task_id="load_fait_embouteillage",
        python_callable=task_load_fait_embouteillage,
    )

    t_refresh_vues = PythonOperator(
        task_id="refresh_vues_olap",
        python_callable=task_refresh_vues_olap,
    )

    fin_pipeline = EmptyOperator(task_id="fin_pipeline")

    # ── Graphe de dépendances ──────────────────────────────────────
    debut_pipeline >> [t_extract_osm, t_extract_meteo]
    [t_extract_osm, t_extract_meteo] >> t_generate_trafic
    t_generate_trafic >> [t_load_dim_temps, t_load_dim_lieu]
    [t_load_dim_temps, t_load_dim_lieu] >> t_load_fait
    t_load_fait >> t_refresh_vues >> fin_pipeline
