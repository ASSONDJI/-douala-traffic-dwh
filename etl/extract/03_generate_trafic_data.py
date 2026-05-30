import pandas as pd
import numpy as np
import os
from datetime import datetime

OUTPUT_DIR = "data/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

np.random.seed(42)

print("=" * 60)
print("  GENERATION DONNEES TRAFIC — Douala 2023-2024")
print("=" * 60)

print("\n[1/6] Chargement des axes critiques OSM...")
axes_df = pd.read_csv("data/raw/osm/axes_critiques_douala.csv")
# 20 axes critiques × 2 ans × 5min = ~2 millions de lignes (optimal)
axes_df = axes_df.nlargest(20, 'longueur_km').reset_index(drop=True)
print(f"      {len(axes_df)} axes critiques selectionnes")

print("\n[2/6] Chargement météo historique...")
meteo_df = pd.read_csv("data/raw/meteo/meteo_douala_2022_2024.csv")
meteo_df['date_heure'] = pd.to_datetime(meteo_df['date_heure'])
meteo_df = meteo_df.set_index('date_heure')
print(f"      {len(meteo_df):,} heures de meteo chargees")

print("\n[3/6] Parametrage des patterns de trafic Douala...")

PROFIL_HORAIRE = {
     0: 0.08,  1: 0.05,  2: 0.04,  3: 0.03,  4: 0.04,  5: 0.12,
     6: 0.45,  7: 0.85,  8: 1.00,  9: 0.80, 10: 0.65, 11: 0.70,
    12: 0.75, 13: 0.72, 14: 0.68, 15: 0.75, 16: 0.90, 17: 1.00,
    18: 0.95, 19: 0.80, 20: 0.60, 21: 0.40, 22: 0.25, 23: 0.15,
}

FACTEUR_JOUR = {
    0: 1.00, 1: 1.05, 2: 1.02, 3: 1.05,
    4: 1.15, 5: 0.70, 6: 0.45,
}

FACTEUR_METEO = {
    'Ensoleille':   1.00,
    'Nuageux':      1.00,
    'Pluie legere': 1.25,
    'Pluie forte':  1.60,
    'Orage':        2.10,
}

VITESSE_LIBRE = {
    'Voie rapide':       70,
    'Avenue principale': 50,
    'Rue secondaire':    30,
    'Piste':             20,
}

VOLUME_BASE = {
    'Voie rapide':       80,
    'Avenue principale': 50,
    'Rue secondaire':    20,
    'Piste':             8,
}

def niveau_service(indice):
    if indice < 1.11:   return 'A'
    elif indice < 1.43: return 'B'
    elif indice < 2.00: return 'C'
    elif indice < 2.50: return 'D'
    elif indice < 4.00: return 'E'
    else:               return 'F'

print("\n[4/6] Generation vectorisee des mesures...")

periodes = pd.date_range(start='2023-01-01', end='2024-12-31 23:55', freq='5min')
print(f"      {len(periodes):,} periodes x {len(axes_df)} axes = {len(periodes)*len(axes_df):,} mesures")

# Construction vectorisée — beaucoup plus rapide que les boucles imbriquées
all_chunks = []

for _, axe in axes_df.iterrows():
    type_route  = axe['type_route']
    vit_libre   = float(VITESSE_LIBRE.get(type_route, 40))
    vol_base    = float(VOLUME_BASE.get(type_route, 20))
    longueur_km = float(axe['longueur_km'])

    df_axe = pd.DataFrame({'date_heure': periodes})
    df_axe['heure']      = df_axe['date_heure'].dt.hour
    df_axe['jour_sem']   = df_axe['date_heure'].dt.dayofweek
    df_axe['heure_meteo']= df_axe['date_heure'].dt.floor('h')

    # Facteurs temporels vectorisés
    df_axe['facteur_h'] = df_axe['heure'].map(PROFIL_HORAIRE)
    df_axe['facteur_j'] = df_axe['jour_sem'].map(FACTEUR_JOUR)

    # Joindre la météo
    df_axe = df_axe.join(
        meteo_df[['condition_meteo','pluie_mm','temperature_c']],
        on='heure_meteo', how='left'
    )
    df_axe['condition_meteo'] = df_axe['condition_meteo'].fillna('Nuageux')
    df_axe['pluie_mm']        = df_axe['pluie_mm'].fillna(0.0)
    df_axe['temperature_c']   = df_axe['temperature_c'].fillna(26.0)
    df_axe['coeff_meteo']     = df_axe['condition_meteo'].map(FACTEUR_METEO).fillna(1.0)

    # Calculs vectorisés
    facteur_total = df_axe['facteur_h'] * df_axe['facteur_j']

    df_axe['volume_vehicules'] = np.maximum(0,
        np.random.normal(
            vol_base * facteur_total,
            vol_base * facteur_total * 0.15
        )
    ).astype(int)

    indice_base = 1.0 + (facteur_total - 0.3) * df_axe['coeff_meteo']
    df_axe['indice_congestion'] = np.maximum(1.0,
        np.random.normal(indice_base, 0.12)
    ).round(4)

    df_axe['vitesse_moyenne_kmh']      = (vit_libre / df_axe['indice_congestion']).clip(lower=2.0).round(2)
    df_axe['vitesse_libre_kmh']        = vit_libre
    df_axe['densite_vehicules_km']     = (df_axe['volume_vehicules'] / max(longueur_km, 0.1)).round(3)
    df_axe['temps_reference_min']      = round((longueur_km / vit_libre) * 60, 2)
    df_axe['temps_parcours_min']       = (longueur_km / df_axe['vitesse_moyenne_kmh'] * 60).round(2)
    df_axe['delai_supplementaire_min'] = (df_axe['temps_parcours_min'] - df_axe['temps_reference_min']).clip(lower=0).round(2)
    df_axe['longueur_bouchon_km']      = ((df_axe['indice_congestion'] - 2.0).clip(lower=0) / 2.0 * longueur_km).round(3)
    df_axe['niveau_service']           = df_axe['indice_congestion'].apply(niveau_service)
    df_axe['flag_incident']            = np.random.random(len(df_axe)) < 0.002

    df_axe['code_segment'] = axe['code_segment']
    df_axe['nom_segment']  = axe['nom_segment']
    df_axe['type_route']   = type_route
    df_axe['lat_centre']   = axe['lat_centre']
    df_axe['lon_centre']   = axe['lon_centre']

    colonnes_finales = [
        'date_heure','code_segment','nom_segment','type_route',
        'condition_meteo','pluie_mm','temperature_c',
        'volume_vehicules','vitesse_moyenne_kmh','vitesse_libre_kmh',
        'indice_congestion','niveau_service','densite_vehicules_km',
        'temps_parcours_min','temps_reference_min','delai_supplementaire_min',
        'longueur_bouchon_km','flag_incident','lat_centre','lon_centre',
    ]
    all_chunks.append(df_axe[colonnes_finales])
    print(f"      axe {_ + 1:>2}/20 traite : {axe['nom_segment'][:40]}")

print("\n[5/6] Concatenation...")
df_final = pd.concat(all_chunks, ignore_index=True)

print("\n[6/6] Export CSV...")
output_path = f"{OUTPUT_DIR}/trafic_douala_2023_2024.csv"
df_final.to_csv(output_path, index=False, encoding='utf-8')

print(f"\n  Total mesures          : {len(df_final):,}")
print(f"  Axes couverts          : {df_final['code_segment'].nunique()}")
print(f"  Volume moyen / mesure  : {df_final['volume_vehicules'].mean():.1f} vehicules")
print(f"  Vitesse moyenne        : {df_final['vitesse_moyenne_kmh'].mean():.1f} km/h")
print(f"  Indice congestion moy  : {df_final['indice_congestion'].mean():.2f}")
print(f"\n  Repartition LOS :")
for los, cnt in df_final['niveau_service'].value_counts().sort_index().items():
    pct = 100 * cnt / len(df_final)
    print(f"    LOS {los} : {cnt:>7,}  ({pct:.1f}%)")
print(f"\n  Fichier : {output_path}")
print(f"  Taille  : {os.path.getsize(output_path)/1024/1024:.1f} MB")

print("\n" + "=" * 60)
print("  GENERATION TERMINEE")
print("=" * 60)
