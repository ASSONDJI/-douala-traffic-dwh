import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "dbname": "douala_traffic_dwh",
    "user": "dwh_admin", "password": "Douala2024!"
}

print("=" * 60)
print("  CHARGEMENT DIM_LIEU")
print("=" * 60)

print("\n[1/3] Lecture des segments OSM...")
df = pd.read_csv("data/raw/osm/segments_douala.csv")
print(f"      {len(df):,} segments charges")

print("\n[2/3] Preparation des enregistrements...")

def detecter_quartier(nom):
    nom_l = str(nom).lower()
    quartiers = {
        'akwa': 'Akwa', 'bonanjo': 'Bonanjo', 'bonapriso': 'Bonapriso',
        'bassa': 'Bassa', 'ndokoti': 'Ndokoti', 'deido': 'Deido',
        'bonaberi': 'Bonaberi', 'new bell': 'New Bell', 'newbell': 'New Bell',
        'mboppi': 'Mboppi', 'wouri': 'Centre', 'joss': 'Bonanjo',
    }
    for kw, q in quartiers.items():
        if kw in nom_l:
            return q
    return 'Douala'

def detecter_arrondissement(quartier):
    mapping = {
        'Akwa': 'Douala 1er', 'Bonanjo': 'Douala 1er',
        'Bonapriso': 'Douala 1er', 'Deido': 'Douala 2e',
        'New Bell': 'Douala 2e', 'Ndokoti': 'Douala 3e',
        'Bassa': 'Douala 3e', 'Mboppi': 'Douala 3e',
        'Bonaberi': 'Douala 4e', 'Centre': 'Douala 1er',
        'Douala': 'Douala 5e',
    }
    return mapping.get(quartier, 'Douala 5e')

records = []
for _, row in df.iterrows():
    quartier       = detecter_quartier(row['nom_segment'])
    arrondissement = detecter_arrondissement(quartier)
    records.append((
        str(row['code_segment']),
        str(row['nom_segment']),
        str(row['nom_segment']),
        str(row['type_route']),
        quartier,
        arrondissement,
        'Douala', 'Littoral', 'Cameroun',
        row['lat_debut']  if pd.notna(row['lat_debut'])  else None,
        row['lon_debut']  if pd.notna(row['lon_debut'])  else None,
        row['lat_fin']    if pd.notna(row['lat_fin'])    else None,
        row['lon_fin']    if pd.notna(row['lon_fin'])    else None,
        row['lat_centre'] if pd.notna(row['lat_centre']) else None,
        row['lon_centre'] if pd.notna(row['lon_centre']) else None,
        float(row['longueur_km']),
        int(row['nombre_voies']),
        int(row['capacite_vehicules_h']),
        False, False, False,
        bool(row['est_axe_critique']),
        None,
        'OpenStreetMap',
    ))

print(f"      {len(records):,} enregistrements prets")

print("\n[3/3] Insertion dans PostgreSQL...")
conn = psycopg2.connect(**DB_CONFIG)
cur  = conn.cursor()

sql = """
    INSERT INTO warehouse.dim_lieu (
        code_segment, nom_segment, axe_principal, type_route,
        quartier, arrondissement, commune, region, pays,
        latitude_debut, longitude_debut, latitude_fin, longitude_fin,
        latitude_centre, longitude_centre,
        longueur_km, nombre_voies, capacite_vehicules_h,
        a_feux_circulation, a_rond_point, est_pont,
        est_axe_critique, zone_type, source_donnee
    ) VALUES %s
    ON CONFLICT DO NOTHING
"""

BATCH = 5000
total = 0
for i in range(0, len(records), BATCH):
    execute_values(cur, sql, records[i:i+BATCH], page_size=BATCH)
    conn.commit()
    total += len(records[i:i+BATCH])
    print(f"      {total:,} / {len(records):,} inseres...")

cur.close()
conn.close()

print(f"\n  Total insere : {total:,} segments")
print("\n" + "=" * 60)
print("  DIM_LIEU CHARGEE")
print("=" * 60)
