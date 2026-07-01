# dbt — Couche analytique du Suivi des bennes

Projet **dbt** qui transforme les tables opérationnelles (Postgres) en une couche
analytique propre (modélisation faits / dimensions + tests de données).

## Architecture

```
sources (public.*)          tables de l'application
        │
        ▼
staging/  (vues)            nettoyage / renommage 1:1
   stg_sites, stg_releves, stg_bennes, stg_evenements
        │
        ▼
marts/    (tables)          modèles analytiques
   dim_site                 dimension déchèterie (+ secteur est/ouest)
   fct_releve_benne         fait : 1 ligne par benne et par relevé
   mart_taux_quotidien      taux moyen/max & alertes par jour et par site
   mart_evenements_mensuels tassements & rotations par mois et par site
```

## Pré-requis

```bash
pip install dbt-postgres
```

## Configuration

La connexion est dans `profiles.yml` (ce dossier), paramétrée par variables
d'environnement. Le mot de passe n'est **jamais** en clair :

```bash
export DBT_PASSWORD='<mot de passe Postgres>'
# valeurs par défaut : host=postgres, db=sotrema_bennes, user=sotrema, schema=analytics
```

> Le `host` par défaut (`postgres`) correspond au service docker-compose. Depuis la
> machine hôte, exporte `DBT_HOST=localhost` (si le port 5432 est publié) ou lance
> dbt dans un conteneur du même réseau Docker.

## Commandes

```bash
cd dbt
dbt debug   --profiles-dir .   # vérifie la connexion
dbt run     --profiles-dir .   # construit staging + marts
dbt test    --profiles-dir .   # exécute tous les tests de données
dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .  # doc + lignage
```

Les modèles sont matérialisés dans le schéma `analytics` (vues pour staging,
tables pour marts). Ils ne modifient jamais les tables de l'application.
