# Sauvegarde de la base

Sauvegarde quotidienne automatique de PostgreSQL (dump compressé), avec purge.

## Automatique (cron)
Une tâche cron utilisateur lance la sauvegarde **chaque jour à 02h30** :

```
30 2 * * * .../deploy/backup/backup-db.sh >> .../deploy/backup/backup.log 2>&1
```

- Les dumps sont dans `deploy/backup/dumps/` (non versionnés).
- Rétention : **14 jours** (les plus anciens sont supprimés automatiquement).
- Journal : `deploy/backup/backup.log`.

Vérifier la planification : `crontab -l` · démon : `pgrep -x cron`.

## Manuel

```bash
make backup                     # sauvegarde immédiate
# ou
./deploy/backup/backup-db.sh
```

## Restauration

⚠️ Écrase les données actuelles (le dump contient les DROP/CREATE).

```bash
make restore FILE=deploy/backup/dumps/sotrema_bennes_AAAAMMJJ-HHMMSS.sql.gz
# ou
./deploy/backup/restore-db.sh <fichier.sql.gz>
```

## Copie hors-serveur (recommandée)
Une sauvegarde sur le même serveur ne protège **pas** d'une panne disque. Pour
recopier automatiquement chaque dump ailleurs, définir `BACKUP_MIRROR` vers un
dossier monté (NAS / partage réseau) :

```
30 2 * * * BACKUP_MIRROR=/mnt/nas/bennes .../deploy/backup/backup-db.sh >> .../backup.log 2>&1
```

Best-effort : si le dossier est absent/non monté, la sauvegarde locale réussit
quand même et un avertissement est journalisé.

## Réglages (variables d'environnement)
`BACKUP_DIR`, `BACKUP_RETENTION` (jours), `BACKUP_MIRROR`, `PG_CONTAINER`,
`POSTGRES_DB`, `POSTGRES_USER`.
