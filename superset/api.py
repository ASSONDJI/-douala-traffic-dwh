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

@app.route('/api/axes_critiques')
def axes_critiques():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT axe_principal, quartier, arrondissement,
               ROUND(indice_cong_moyen::numeric, 3)      AS indice_cong_moyen,
               ROUND(vitesse_moyenne::numeric, 1)        AS vitesse_moyenne,
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

@app.route('/api/evolution_mensuelle')
def evolution_mensuelle():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            t.annee, t.mois, t.nom_mois,
            ROUND(AVG(f.indice_congestion)::numeric, 3)   AS congestion_moy,
            ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1) AS vitesse_moy,
            SUM(f.volume_vehicules)                       AS volume_total
        FROM warehouse.fait_embouteillage f
        JOIN warehouse.dim_temps t ON f.id_temps = t.id_temps
        GROUP BY t.annee, t.mois, t.nom_mois
        ORDER BY t.annee, t.mois
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in data])

@app.route('/api/carte_axes')
def carte_axes():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            l.nom_segment, l.quartier, l.arrondissement,
            l.axe_principal, l.type_route,
            ROUND(l.latitude_centre::numeric, 6)        AS lat,
            ROUND(l.longitude_centre::numeric, 6)       AS lon,
            ROUND(AVG(f.indice_congestion)::numeric, 3) AS congestion_moy,
            ROUND(AVG(f.vitesse_moyenne_kmh)::numeric,1)AS vitesse_moy,
            COUNT(*)                                    AS nb_mesures
        FROM warehouse.fait_embouteillage f
        JOIN warehouse.dim_lieu l ON f.id_lieu = l.id_lieu
        WHERE l.latitude_centre IS NOT NULL
          AND l.longitude_centre IS NOT NULL
        GROUP BY l.nom_segment, l.quartier, l.arrondissement,
                 l.axe_principal, l.type_route,
                 l.latitude_centre, l.longitude_centre
        ORDER BY congestion_moy DESC
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in data])

@app.route('/api/filtres/quartiers')
def filtres_quartiers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT quartier
        FROM warehouse.dim_lieu
        WHERE est_actif = TRUE
        ORDER BY quartier
    """)
    data = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(data)

@app.route('/api/axes_critiques_filtres')
def axes_critiques_filtres():
    from flask import request
    quartier = request.args.get('quartier', '')
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    where = "WHERE 1=1"
    params = []
    if quartier:
        where += " AND quartier = %s"
        params.append(quartier)
    cur.execute(f"""
        SELECT axe_principal, quartier, arrondissement,
               ROUND(indice_cong_moyen::numeric, 3) AS indice_cong_moyen,
               ROUND(vitesse_moyenne::numeric, 1)   AS vitesse_moyenne,
               nb_observations,
               ROUND(delai_total_cumule_min::numeric, 0) AS delai_total
        FROM datamart.vm_axes_critiques
        {where}
        ORDER BY indice_cong_moyen DESC
        LIMIT 10
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in data])

@app.route('/api/profil_semaine_filtre')
def profil_semaine_filtre():
    from flask import request
    quartier = request.args.get('quartier', '')
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if quartier:
        cur.execute("""
            SELECT t.nom_jour, t.jour_semaine, t.heure,
                   ROUND(AVG(f.indice_congestion)::numeric, 3) AS indice_cong_moyen,
                   ROUND(AVG(f.vitesse_moyenne_kmh)::numeric, 1) AS vitesse_moy,
                   SUM(f.volume_vehicules) AS volume_total
            FROM warehouse.fait_embouteillage f
            JOIN warehouse.dim_temps t ON f.id_temps = t.id_temps
            JOIN warehouse.dim_lieu  l ON f.id_lieu  = l.id_lieu
            WHERE l.quartier = %s
            GROUP BY t.nom_jour, t.jour_semaine, t.heure
            ORDER BY t.jour_semaine, t.heure
        """, [quartier])
    else:
        cur.execute("""
            SELECT nom_jour, jour_semaine, heure,
                   ROUND(indice_cong_moyen::numeric, 3) AS indice_cong_moyen,
                   ROUND(vitesse_moy::numeric, 1) AS vitesse_moy,
                   volume_total
            FROM datamart.vm_profil_semaine
            ORDER BY jour_semaine, heure
        """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in data])    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)

