#!/usr/bin/env bash
# Génère une CSR (Certificate Signing Request) à partir de la clé privée
# existante, à transmettre à l'AC interne Sotrema pour signature.
#
# Le certificat renvoyé par l'AC remplacera fullchain.pem (même clé, aucun
# rebuild). Conserver privkey.pem : c'est la clé associée à cette CSR.
#
# Usage : HOST=bennes.sotrema-environnement.local IP=220.220.220.24 ./generer-csr.sh
set -euo pipefail
cd "$(dirname "$0")"

HOST="${HOST:-bennes.sotrema-environnement.local}"
IP="${IP:-}"

if [ ! -f privkey.pem ]; then
  echo "privkey.pem introuvable : lance d'abord ./generer-cert.sh" >&2
  exit 1
fi

SAN="DNS:${HOST},DNS:localhost,IP:127.0.0.1"
[ -n "${IP}" ] && SAN="${SAN},IP:${IP}"

openssl req -new -key privkey.pem -out "${HOST}.csr" \
  -subj "/CN=${HOST}" \
  -addext "subjectAltName=${SAN}"

echo "✓ ${HOST}.csr généré (SAN : ${SAN})."
echo "  → À transmettre à l'IT / l'AC interne pour signature."
echo "  → Récupérer le certificat signé, le placer en 'fullchain.pem', puis :"
echo "     docker restart suivi-bennes-dechetterie_frontend_1"
