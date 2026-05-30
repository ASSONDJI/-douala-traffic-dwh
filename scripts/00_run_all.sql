
SCRIPT MAÎTRE — Crée toute la structure du DWH
Exécuter dans l'ordre : \i scripts/00_run_all.sql


\echo ' Création DWH Douala Traffic '
\echo ''

\i /scripts/01_dim_temps.sql
\i /scripts/02_dim_lieu.sql
\i /scripts/03_dim_vehicule.sql
\i /scripts/04_dim_evenement.sql
\i /scripts/05_dim_trajet.sql
\i /scripts/06_dim_capteur.sql
\i /scripts/07_fait_embouteillage.sql
\i /scripts/08_vues_datamart.sql

\echo ''
\echo ' DWH Douala Traffic — Structure complète créée '
