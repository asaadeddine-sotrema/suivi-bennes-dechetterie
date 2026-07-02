#!/usr/bin/env bash
# Restauration d'une sauvegarde dans la base PostgreSQL.
# ⚠️ Écrase les données actuelles (le dump contient les DROP/CREATE).
#
# Usage : ./restore-db.sh <fichier.sql.gz>
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:${PATH:-}"

FICHIER="${1:-}"
CONTENEUR="${PG_CONTAINER:-suivi-bennes-dechetterie_postgres_1}"
DB="${POSTGRES_DB:-sotrema_bennes}"
USER_DB="${POSTGRES_USER:-sotrema}"

if [ -z "$FICHIER" ] || [ ! -f "$FICHIER" ]; then
    echo "Usage : $0 <fichier.sql.gz>" >&2
    exit 1
fi

echo "⚠️  Cette opération va écraser la base '$DB'. Ctrl-C pour annuler."
read -r -p "Confirmer la restauration de $(basename "$FICHIER") ? [oui/non] " reponse
[ "$reponse" = "oui" ] || { echo "Annulé."; exit 1; }

gunzip -c "$FICHIER" | docker exec -i "$CONTENEUR" psql -U "$USER_DB" -d "$DB" -v ON_ERROR_STOP=1
echo "✓ Restauration terminée."
