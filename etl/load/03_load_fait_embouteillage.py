import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "host": "postgres-dwh", "port": 5432,
    "dbname": "douala_traffic_dwh",
    "user": "dwh_admin", "password": "Douala2024!"
}

print("=" * 60)
print("  CHARGEMENT FAIT_EMBOUTEILLAGE")
print("=" * 60)

conn = psycopg2.connect(**DB_CONFIG)
cur  = conn.cursor()

print("\n[1/5] Chargement des referentiels dimensions...")

cur.execute("SELECT id_temps, date_heure FROM warehouse.dim_temps")
map_temps = {str(r[1])[:16]: r[0] for r in cur.fetchall()}
print(f"      {len(map_temps):,} cles DIM_TEMPS")

cur.execute("SELECT id_lieu, code_segment FROM warehouse.dim_lieu")
map_lieu = {r[1]: r[0] for r in cur.fetchall()}
print(f"      {len(map_lieu):,} cles DIM_LIEU")

cur.execute("SELECT id_evenement, sous_type FROM warehouse.dim_evenement")
map_event = {r[1]: r[0] for r in cur.fetchall()}
print(f"      {len(map_event):,} cles DIM_EVENEMENT")

cur.execute("SELECT id_vehicule, code_vehicule FROM warehouse.dim_vehicule WHERE code_vehicule = 'INCONNU'")
id_vehicule_defaut = cur.fetchone()[0]

cur.execute("SELECT id_capteur, code_capteur FROM warehouse.dim_capteur WHERE code_capteur = 'SIM_PYTHON'")
id_capteur_sim = cur.fetchone()[0]

meteo_to_event = {
    'Ensoleille':   'Ensoleille',
    'Nuageux':      'Nuageux',
    'Pluie legere': 'Pluie legere',
    'Pluie forte':  'Pluie forte',
    'Orage':        'Orage',
}

print("\n[2/5] Lecture du fichier trafic (791 MB)...")
df = pd.read_csv(
    "data/generated/trafic_douala_2023_2024.csv",
    dtype={
        'volume_vehicules': 'int32',
        'flag_incident':    'bool',
        'niveau_service':   'str',
    }
)
print(f"      {len(df):,} mesures lues")

print("\n[3/5] Correspondances clés dimensionnelles...")
df['date_heure_str'] = pd.to_datetime(df['date_heure']).dt.strftime('%Y-%m-%d %H:%M')
df['id_temps']    = df['date_heure_str'].map(map_temps)
df['id_lieu']     = df['code_segment'].map(map_lieu)
df['id_evenement']= df['condition_meteo'].map(meteo_to_event).map(map_event)
df['id_vehicule'] = id_vehicule_defaut
df['id_capteur']  = id_capteur_sim

avant = len(df)
df = df.dropna(subset=['id_temps', 'id_lieu', 'id_evenement'])
print(f"      Lignes valides : {len(df):,} / {avant:,}")

print("\n[4/5] Insertion dans PostgreSQL par batches...")

sql = """
    INSERT INTO warehouse.fait_embouteillage (
        id_temps, id_lieu, id_vehicule, id_evenement, id_capteur,
        volume_vehicules, volume_pce, densite_vehicules_km,
        vitesse_moyenne_kmh, vitesse_libre_kmh,
        indice_congestion, niveau_service, longueur_bouchon_km,
        temps_parcours_min, temps_reference_min, delai_supplementaire_min,
        flag_incident, flag_donnee_manquante, batch_id
    ) VALUES %s
    ON CONFLICT DO NOTHING
"""

BATCH   = 5000
total   = 0
batch_id = 'BATCH_ETL_001'

records = []
for _, row in df.iterrows():
    records.append((
        int(row['id_temps']),
        int(row['id_lieu']),
        int(row['id_vehicule']),
        int(row['id_evenement']),
        int(row['id_capteur']),
        int(row['volume_vehicules']),
        float(row['volume_vehicules']) * 1.0,
        float(row['densite_vehicules_km']),
        float(row['vitesse_moyenne_kmh']),
        float(row['vitesse_libre_kmh']),
        float(row['indice_congestion']),
        str(row['niveau_service']),
        float(row['longueur_bouchon_km']),
        float(row['temps_parcours_min']),
        float(row['temps_reference_min']),
        float(row['delai_supplementaire_min']),
        bool(row['flag_incident']),
        False,
        batch_id,
    ))

    if len(records) == BATCH:
        execute_values(cur, sql, records, page_size=BATCH)
        conn.commit()
        total += BATCH
        records = []
        if total % 200000 == 0:
            print(f"      {total:,} / {len(df):,} inseres...")

if records:
    execute_values(cur, sql, records, page_size=BATCH)
    conn.commit()
    total += len(records)

print(f"\n[5/5] Rafraichissement des vues materialisees...")
cur.execute("REFRESH MATERIALIZED VIEW datamart.vm_trafic_horaire")
cur.execute("REFRESH MATERIALIZED VIEW datamart.vm_axes_critiques")
cur.execute("REFRESH MATERIALIZED VIEW datamart.vm_impact_meteo")
cur.execute("REFRESH MATERIALIZED VIEW datamart.vm_profil_semaine")
conn.commit()

cur.close()
conn.close()

print(f"\n  Total insere : {total:,} faits")
print(f"  Vues OLAP    : rafraichies")
print("\n" + "=" * 60)
print("  FAIT_EMBOUTEILLAGE CHARGE")
print("=" * 60)
