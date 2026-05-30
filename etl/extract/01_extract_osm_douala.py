import osmnx as ox
import pandas as pd
import os
from datetime import datetime

OUTPUT_DIR = "data/raw/osm"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("  EXTRACTION OSM — Réseau routier Douala")
print("=" * 60)

print("\n[1/4] Téléchargement du réseau routier...")
G = ox.graph_from_place("Douala, Cameroun", network_type="drive", simplify=True)
print(f"      {len(G.nodes):,} noeuds  |  {len(G.edges):,} segments")

print("\n[2/4] Conversion en DataFrame...")
nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)

# Réinitialiser l'index MultiIndex en colonnes simples
edges_flat = edges.reset_index()

# Calculer les centroïdes en projetant d'abord en UTM zone 32N
edges_utm      = edges.to_crs(epsg=32632)
centroids_utm  = edges_utm.geometry.centroid
centroids_wgs  = centroids_utm.to_crs(epsg=4326)

# Aligner les index avant assignation
edges_flat = edges_flat.copy()
edges_flat.index = range(len(edges_flat))
centroids_wgs = centroids_wgs.reset_index(drop=True)

edges_flat['lat_centre'] = centroids_wgs.y
edges_flat['lon_centre'] = centroids_wgs.x

edges_flat['lat_debut'] = edges_flat.geometry.apply(lambda g: g.coords[0][1])
edges_flat['lon_debut'] = edges_flat.geometry.apply(lambda g: g.coords[0][0])
edges_flat['lat_fin']   = edges_flat.geometry.apply(lambda g: g.coords[-1][1])
edges_flat['lon_fin']   = edges_flat.geometry.apply(lambda g: g.coords[-1][0])

edges_flat['longueur_km'] = edges_flat['length'] / 1000

print("\n[3/4] Enrichissement des attributs...")

def classifier_route(val):
    if isinstance(val, list):
        val = val[0]
    mapping = {
        'motorway':     'Voie rapide',
        'trunk':        'Voie rapide',
        'primary':      'Avenue principale',
        'secondary':    'Avenue principale',
        'tertiary':     'Rue secondaire',
        'residential':  'Rue secondaire',
        'unclassified': 'Rue secondaire',
        'service':      'Piste',
    }
    return mapping.get(str(val), 'Rue secondaire')

def extraire_voies(val):
    if isinstance(val, list):
        val = val[0] if val else None
    if val is None:
        return 2
    try:
        return int(float(str(val)))
    except Exception:
        return 2

def extraire_nom(val):
    if isinstance(val, list):
        val = val[0] if val else None
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 'Segment sans nom'
    return str(val)

edges_flat['type_route']   = edges_flat['highway'].apply(classifier_route)
edges_flat['nombre_voies'] = edges_flat['lanes'].apply(extraire_voies) \
                             if 'lanes' in edges_flat.columns else 2
edges_flat['nom_segment']  = edges_flat['name'].apply(extraire_nom) \
                             if 'name' in edges_flat.columns \
                             else 'Segment sans nom'

edges_flat['code_segment'] = edges_flat.apply(
    lambda r: f"OSM_{r['u']}_{r['v']}_{r['key']}", axis=1)

capacite_map = {
    'Voie rapide':       2000,
    'Avenue principale': 1500,
    'Rue secondaire':    800,
    'Piste':             400,
}
edges_flat['capacite_vehicules_h'] = edges_flat.apply(
    lambda r: capacite_map.get(r['type_route'], 800) * r['nombre_voies'], axis=1)

axes_critiques_kw = [
    'liberté', 'liberte', 'ndokoti', 'bonabéri', 'bonaberi',
    'akwa', 'bassa', 'deido', 'new bell', 'newbell',
    'bonapriso', 'bonanjo', 'mboppi', 'wouri',
]
edges_flat['est_axe_critique'] = edges_flat['nom_segment'].apply(
    lambda n: any(kw in str(n).lower() for kw in axes_critiques_kw))

print("\n[4/4] Export CSV...")

colonnes = [
    'code_segment', 'nom_segment', 'type_route',
    'longueur_km', 'nombre_voies', 'capacite_vehicules_h',
    'lat_debut', 'lon_debut', 'lat_fin', 'lon_fin',
    'lat_centre', 'lon_centre', 'est_axe_critique',
]
df = edges_flat[colonnes].drop_duplicates(subset=['code_segment']).copy()
df['source_donnee']   = 'OpenStreetMap'
df['date_extraction'] = datetime.now().isoformat()

output_path = f"{OUTPUT_DIR}/segments_douala.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

axes = df[df['est_axe_critique']]
if len(axes) > 0:
    axes.to_csv(f"{OUTPUT_DIR}/axes_critiques_douala.csv", index=False)

print(f"\n  Total segments       : {len(df):,}")
print(f"  Voies rapides        : {(df['type_route']=='Voie rapide').sum():,}")
print(f"  Avenues principales  : {(df['type_route']=='Avenue principale').sum():,}")
print(f"  Rues secondaires     : {(df['type_route']=='Rue secondaire').sum():,}")
print(f"  Axes critiques       : {df['est_axe_critique'].sum():,}")
print(f"  Longueur totale      : {df['longueur_km'].sum():.1f} km")
print(f"\n  Fichier : {output_path}")
print(f"  Axes critiques : data/raw/osm/axes_critiques_douala.csv")

print("\n" + "=" * 60)
print("  EXTRACTION OSM TERMINEE")
print("=" * 60)
