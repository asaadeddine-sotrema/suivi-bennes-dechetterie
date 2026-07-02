# TLS — accès HTTPS de l'application

Le frontend (nginx du conteneur) termine le TLS sur le port **3443**.
Accès : `https://bennes.sotrema-environnement.local:3443`

## Fichiers

| Fichier | Rôle | Versionné ? |
|---|---|---|
| `generer-cert.sh` | Génère un certificat auto-signé | oui |
| `generer-csr.sh` | Génère une CSR pour signature par l'AC interne | oui |
| `fullchain.pem` | Certificat servi par nginx | **non** (gitignore) |
| `privkey.pem` | Clé privée | **non** (gitignore) |
| `*.csr` | Demande de signature | **non** (gitignore) |

La clé privée n'est jamais dans l'image : elle est montée en volume
(`./deploy/tls:/etc/nginx/tls:ro`). Remplacer un certificat ne nécessite
donc **aucun rebuild**, juste un `docker restart`.

## Deux prérequis pour un accès « propre » (sans avertissement, par le nom)

### 1. Résolution DNS
`bennes.sotrema-environnement.local` doit pointer vers l'IP du serveur
(220.220.220.24). Soit un enregistrement A dans le DNS interne (IT), soit,
pour tester, une ligne dans le fichier hosts de chaque poste :

```
220.220.220.24  bennes.sotrema-environnement.local
```

### 2. Certificat approuvé (supprime l'avertissement navigateur)
Faire signer la CSR par l'AC interne Sotrema :

```bash
HOST=bennes.sotrema-environnement.local IP=220.220.220.24 ./generer-csr.sh
# -> transmettre bennes.sotrema-environnement.local.csr à l'IT
```

Récupérer le certificat signé, le placer ici sous le nom `fullchain.pem`
(concaténer la chaîne intermédiaire de l'AC si fournie), puis :

```bash
docker restart suivi-bennes-dechetterie_frontend_1
```

Une fois un certificat approuvé en place, activer HSTS : décommenter la ligne
`Strict-Transport-Security` dans `frontend/nginx.conf` et redéployer.

> À défaut d'AC interne : importer `fullchain.pem` (le certificat auto-signé)
> dans le magasin « Autorités de certification racines de confiance » des
> postes, idéalement via GPO.

## Régénérer un certificat auto-signé

```bash
HOST=bennes.sotrema-environnement.local IP=220.220.220.24 ./generer-cert.sh
docker restart suivi-bennes-dechetterie_frontend_1
```
