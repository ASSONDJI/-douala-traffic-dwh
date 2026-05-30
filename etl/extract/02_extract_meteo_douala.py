import requests
import pandas as pd
import os
from datetime import datetime

OUTPUT_DIR = "data/raw/meteo"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LAT_DOUALA = 4.0511
LON_DOUALA = 9.7679

print("=" * 60)
print("  EXTRACTION METEO — Open-Meteo API Douala")
print("=" * 60)

print("\n[1/4] Appel API Open-Meteo (2022-2024)...")

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude":   LAT_DOUALA,
    "longitude":  LON_DOUALA,
    "start_date": "2022-01-01",
    "end_date":   "2024-12-31",
    "hourly": [
        "temperature_2m",
        "precipitation",
        "rain",
        "relative_humidity_2m",
        "windspeed_10m",
        "weathercode",
        "visibility",
        "cloudcover",
    ],
    "timezone":        "Africa/Douala",
    "wind_speed_unit": "kmh",
}

response = requests.get(url, params=params, timeout=120)

if response.status_code != 200:
    print(f"  Erreur API : {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
print(f"      Position confirmee : {data['latitude']}N  {data['longitude']}E")

print("\n[2/4] Construction du DataFrame...")

hourly = data['hourly']
df = pd.DataFrame({
    'date_heure':            pd.to_datetime(hourly['time']),
    'temperature_c':         hourly['temperature_2m'],
    'precipitation_mm':      hourly['precipitation'],
    'pluie_mm':              hourly['rain'],
    'humidite_pct':          hourly['relative_humidity_2m'],
    'vent_kmh':              hourly['windspeed_10m'],
    'code_meteo_wmo':        hourly['weathercode'],
    'visibilite_m':          hourly['visibility'],
    'couverture_nuages_pct': hourly['cloudcover'],
})

print("\n[3/4] Classification des conditions meteo...")

def classifier_meteo(row):
    pluie = row['pluie_mm'] if pd.notna(row['pluie_mm']) else 0
    code  = row['code_meteo_wmo'] if pd.notna(row['code_meteo_wmo']) else 0
    if pluie > 10 or code >= 95:
        return 'Orage'
    elif pluie > 2.5:
        return 'Pluie forte'
    elif pluie > 0.1:
        return 'Pluie legere'
    elif code in [1, 2, 3]:
        return 'Nuageux'
    else:
        return 'Ensoleille'

df['condition_meteo'] = df.apply(classifier_meteo, axis=1)

impact_map = {
    'Ensoleille':   1.0,
    'Nuageux':      1.0,
    'Pluie legere': 1.2,
    'Pluie forte':  1.6,
    'Orage':        2.0,
}
df['coefficient_impact_trafic'] = df['condition_meteo'].map(impact_map)

df['annee']        = df['date_heure'].dt.year
df['mois']         = df['date_heure'].dt.month
df['jour']         = df['date_heure'].dt.day
df['heure']        = df['date_heure'].dt.hour
df['jour_semaine'] = df['date_heure'].dt.dayofweek

print("\n[4/4] Export CSV...")

output_path = f"{OUTPUT_DIR}/meteo_douala_2022_2024.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print(f"\n  Total enregistrements    : {len(df):,}")
print(f"  Temperature moyenne      : {df['temperature_c'].mean():.1f} C")
print(f"  Precipitations totales   : {df['precipitation_mm'].sum():.0f} mm")
print(f"\n  Repartition conditions meteo :")
for condition, count in df['condition_meteo'].value_counts().items():
    pct = 100 * count / len(df)
    print(f"    {condition:<15} : {count:>6,} heures  ({pct:.1f}%)")

print(f"\n  Fichier : {output_path}")

print("\n" + "=" * 60)
print("  EXTRACTION METEO TERMINEE")
print("=" * 60)
