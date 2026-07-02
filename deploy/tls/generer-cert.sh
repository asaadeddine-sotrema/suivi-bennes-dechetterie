#!/usr/bin/env bash
# Génère un certificat TLS auto-signé pour l'accès HTTPS sur le réseau interne.
#
# Usage :
#   ./generer-cert.sh                 # CN=localhost + SAN localhost/127.0.0.1
#   HOST=bennes.sotrema.lan ./generer-cert.sh
#   HOST=bennes.sotrema.lan IP=220.220.220.24 ./generer-cert.sh
#
# Produit fullchain.pem + privkey.pem dans ce dossier. Pour passer à un vrai
# certificat (AC interne / Let's Encrypt), il suffit de remplacer ces deux
# fichiers en gardant les mêmes noms — aucun rebuild nécessaire.
set -euo pipefail
cd "$(dirname "$0")"

HOST="${HOST:-localhost}"
IP="${IP:-}"
JOURS="${JOURS:-825}"

# Construction des SAN (obligatoires : les navigateurs ignorent le CN seul)
SAN="DNS:${HOST}"
[ "${HOST}" != "localhost" ] && SAN="${SAN},DNS:localhost"
SAN="${SAN},IP:127.0.0.1"
[ -n "${IP}" ] && SAN="${SAN},IP:${IP}"

echo "→ Génération d'un certificat auto-signé"
echo "  CN  : ${HOST}"
echo "  SAN : ${SAN}"
echo "  Validité : ${JOURS} jours"

openssl req -x509 -newkey rsa:2048 -sha256 -nodes \
  -keyout privkey.pem -out fullchain.pem -days "${JOURS}" \
  -subj "/CN=${HOST}" \
  -addext "subjectAltName=${SAN}"

chmod 600 privkey.pem
echo "✓ fullchain.pem + privkey.pem générés."
echo "  (Certificat auto-signé : les navigateurs afficheront un avertissement"
echo "   tant que le certificat n'est pas approuvé / signé par une AC interne.)"
