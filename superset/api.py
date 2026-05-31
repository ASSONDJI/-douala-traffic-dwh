from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "dbname": "douala_traffic_dwh",
    "user": "dwh_admin", "password": "Douala2024!"
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/api/axes_critiques')
def axes_critiques():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT axe_principal, quartier, arrondissement,
               ROUND(indice_cong_moyen::numeric, 3) AS indice_cong_moyen,
               ROUND(vitesse_moyenne::numeric, 1)   AS vitesse_moyenne,
               nb_observations,
               ROUND(delai_total_cumule_min::numeric, 0) AS delai_total,
               pct_temps_sature
        FROM datamart.vm_axes_critiques
        ORDER BY indice_cong_moyen DESC
        LIMIT 10
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in data])

@app.route('/api/impact_meteo')
def impact_meteo():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT condition_meteo, impact_trafic,
               ROUND(indice_cong_moyen::numeric, 3) AS indice_cong_moyen,
               ROUND(vitesse_moy::numeric, 1)       AS vitesse_moy,
               nb_observations,
               ROUND(delai_moy_min::numeric, 2)     AS delai_moy_min
        FROM datamart.vm_impact_meteo
        ORDER BY indice_cong_moyen DESC
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in data])

@app.route('/api/profil_semaine')
def profil_semaine():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT nom_jour, jour_semaine, heure,
               ROUND(indice_cong_moyen::numeric, 3) AS indice_cong_moyen,
               ROUND(vitesse_moy::numeric, 1)       AS vitesse_moy,
               volume_total
        FROM datamart.vm_profil_semaine
        ORDER BY jour_semaine, heure
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in data])

@app.route('/api/stats_globales')
def stats_globales():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            COUNT(*)                                        AS total_mesures,
            ROUND(AVG(indice_congestion)::numeric, 3)       AS congestion_moyenne,
            ROUND(AVG(vitesse_moyenne_kmh)::numeric, 1)     AS vitesse_moyenne,
            SUM(volume_vehicules)                           AS volume_total,
            SUM(CASE WHEN flag_incident THEN 1 ELSE 0 END)  AS total_incidents,
            SUM(CASE WHEN niveau_service = 'F'
                     THEN 1 ELSE 0 END)                     AS heures_bloquees
        FROM warehouse.fait_embouteillage
    """)
    data = cur.fetchone()
    cur.close(); conn.close()
    return jsonify(dict(data))

@app.route('/api/evolution_mensuelle')
def evolution_mensuelle():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            t.annee, t.mois, t.nom_mois,
            ROUND(AVG(f.indice_congestion)::numeric, 3) AS congestion_moy,
            ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1) AS vitesse_moy,
            SUM(f.volume_vehicules) AS volume_total
        FROM warehouse.fait_embouteillage f
        JOIN warehouse.dim_temps t ON f.id_temps = t.id_temps
        GROUP BY t.annee, t.mois, t.nom_mois
        ORDER BY t.annee, t.mois
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in data])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
