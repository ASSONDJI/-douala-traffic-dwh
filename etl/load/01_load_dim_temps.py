import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "douala_traffic_dwh",
    "user":     "dwh_admin",
    "password": "Douala2024!"
}

JOURS_FERIES_CAMEROUN = {
    "01-01": "Jour de l'An",
    "02-11": "Fete de la Jeunesse",
    "05-01": "Fete du Travail",
    "05-20": "Fete Nationale",
    "08-15": "Assomption",
    "10-01": "Fete de l'Unification",
    "12-25": "Noel",
}

print("=" * 60)
print("  CHARGEMENT DIM_TEMPS")
print("=" * 60)

print("\n[1/3] Generation des periodes 5 minutes (2022-2026)...")
periodes = pd.date_range(start='2022-01-01', end='2026-12-31 23:55', freq='5min')
print(f"      {len(periodes):,} periodes generees")

print("\n[2/3] Construction des enregistrements...")

NOM_MOIS = {
    1:'Janvier', 2:'Fevrier', 3:'Mars', 4:'Avril',
    5:'Mai', 6:'Juin', 7:'Juillet', 8:'Aout',
    9:'Septembre', 10:'Octobre', 11:'Novembre', 12:'Decembre'
}
NOM_JOUR = {
    0:'Lundi', 1:'Mardi', 2:'Mercredi', 3:'Jeudi',
    4:'Vendredi', 5:'Samedi', 6:'Dimanche'
}

def tranche_horaire(h):
    if 6 <= h < 9:   return 'Pointe matin (6h-9h)'
    elif 9 <= h < 17: return 'Journee (9h-17h)'
    elif 17 <= h < 20: return 'Pointe soir (17h-20h)'
    else:             return 'Nuit (20h-6h)'

def saison_cameroun(m):
    if m in [11, 12, 1, 2, 3]: return 'Grande saison seche (Nov-Mar)'
    elif m in [7, 8, 9, 10]:   return 'Grande saison pluies (Jul-Oct)'
    else:                       return 'Petite saison seche (Avr-Jun)'

records = []
for ts in periodes:
    mmjj      = ts.strftime('%m-%d')
    est_ferie = mmjj in JOURS_FERIES_CAMEROUN
    nom_ferie = JOURS_FERIES_CAMEROUN.get(mmjj)
    heure     = ts.hour
    est_pointe = heure in range(6,9) or heure in range(17,20)

    records.append((
        int(ts.strftime('%Y%m%d%H%M')),  # id_temps
        ts.date(),                        # date_complete
        ts,                               # date_heure
        ts.year,                          # annee
        ts.quarter,                       # trimestre
        ts.month,                         # mois
        NOM_MOIS[ts.month],               # nom_mois
        ts.isocalendar()[1],              # semaine_annee
        ts.day,                           # jour_mois
        ts.dayofweek,                     # jour_semaine
        NOM_JOUR[ts.dayofweek],           # nom_jour
        heure,                            # heure
        ts.minute,                        # minute
        ts.dayofweek >= 5,                # est_weekend
        est_ferie,                        # est_jour_ferie_cm
        nom_ferie,                        # nom_jour_ferie
        tranche_horaire(heure),           # tranche_horaire
        est_pointe,                       # est_heure_pointe
        saison_cameroun(ts.month),        # saison_cameroun
    ))

print(f"      {len(records):,} enregistrements prets")

print("\n[3/3] Insertion dans PostgreSQL...")
conn = psycopg2.connect(**DB_CONFIG)
cur  = conn.cursor()

sql = """
    INSERT INTO warehouse.dim_temps (
        id_temps, date_complete, date_heure,
        annee, trimestre, mois, nom_mois, semaine_annee,
        jour_mois, jour_semaine, nom_jour, heure, minute,
        est_weekend, est_jour_ferie_cm, nom_jour_ferie,
        tranche_horaire, est_heure_pointe, saison_cameroun
    ) VALUES %s
    ON CONFLICT (id_temps) DO NOTHING
"""

BATCH = 10000
total_insere = 0
for i in range(0, len(records), BATCH):
    batch = records[i:i+BATCH]
    execute_values(cur, sql, batch, page_size=BATCH)
    conn.commit()
    total_insere += len(batch)
    if total_insere % 100000 == 0:
        print(f"      {total_insere:,} / {len(records):,} inseres...")

cur.close()
conn.close()

print(f"\n  Total insere : {total_insere:,} lignes")
print("\n" + "=" * 60)
print("  DIM_TEMPS CHARGE")
print("=" * 60)
