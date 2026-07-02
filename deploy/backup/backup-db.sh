#!/usr/bin/env bash
# Sauvegarde de la base PostgreSQL (dump compressé, horodaté) + purge des anciennes.
#
# Prévu pour tourner via cron. Variables surchargeables :
#   PG_CONTAINER (déf. suivi-bennes-dechetterie_postgres_1)
#   POSTGRES_DB / POSTGRES_USER (déf. sotrema_bennes / sotrema)
#   BACKUP_DIR (déf. ./dumps à côté du script)
#   BACKUP_RETENTION (déf. 14 jours)
set -euo pipefail

# cron a un PATH minimal : on s'assure que docker est joignable.
export PATH="/usr/local/bin:/usr/bin:/bin:${PATH:-}"

CONTENEUR="${PG_CONTAINER:-suivi-bennes-dechetterie_postgres_1}"
DB="${POSTGRES_DB:-sotrema_bennes}"
USER_DB="${POSTGRES_USER:-sotrema}"
DEST="${BACKUP_DIR:-$(cd "$(dirname "$0")" && pwd)/dumps}"
RETENTION="${BACKUP_RETENTION:-14}"

mkdir -p "$DEST"
horodatage="$(date +%Y%m%d-%H%M%S)"
fichier="$DEST/sotrema_bennes_${horodatage}.sql.gz"

# --clean --if-exists : le dump inclut les DROP, la restauration est donc complète.
docker exec "$CONTENEUR" pg_dump -U "$USER_DB" --clean --if-exists "$DB" | gzip > "$fichier"

if [ ! -s "$fichier" ]; then
    echo "$(date '+%F %T') ERREUR : dump vide, suppression de $fichier" >&2
    rm -f "$fichier"
    exit 1
fi

# Purge des sauvegardes au-delà de la rétention.
find "$DEST" -name 'sotrema_bennes_*.sql.gz' -mtime +"$RETENTION" -delete

echo "$(date '+%F %T') OK : $fichier ($(du -h "$fichier" | cut -f1))"

# Copie hors-serveur (optionnelle) : définir BACKUP_MIRROR vers un dossier monté
# (NAS / partage réseau). Best-effort : n'échoue pas la sauvegarde locale.
if [ -n "${BACKUP_MIRROR:-}" ]; then
    if [ -d "$BACKUP_MIRROR" ] && cp "$fichier" "$BACKUP_MIRROR/"; then
        find "$BACKUP_MIRROR" -name 'sotrema_bennes_*.sql.gz' -mtime +"$RETENTION" -delete 2>/dev/null || true
        echo "$(date '+%F %T') OK : copie miroir -> $BACKUP_MIRROR"
    else
        echo "$(date '+%F %T') ATTENTION : copie miroir vers '$BACKUP_MIRROR' échouée (dossier absent/non monté ?)" >&2
    fi
fi
