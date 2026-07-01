"""Test interactif de récupération des mails Kizeo via le flux device-code (délégué).

Permet de valider GRATUITEMENT, avec TA propre boîte M365, toute la chaîne
« connexion → liste des mails → téléchargement du PDF → parsing », sans la
permission « Application » (donc sans consentement admin obligatoire — sauf si
le tenant l'exige).

Prérequis (dans .env) :
    AZURE_CLIENT_ID = <Application (client) ID de l'app registration>
    AZURE_TENANT_ID = <Directory (tenant) ID>
    (pas besoin de AZURE_CLIENT_SECRET pour ce flux)

L'app registration doit avoir :
    - Authentication → « Allow public client flows » = Yes
    - API permissions → Microsoft Graph → Delegated → Mail.Read

Lancement (en interactif, depuis le conteneur backend) :
    docker exec -it suivi-bennes-dechetterie_backend_1 \
        sh -c "cd /app && PYTHONPATH=/app python -m backend.scripts.test_mail_device_code"
"""
import sys
import os
import base64

import httpx
import msal

from backend.config import settings
from backend.services.pdf_parser import parse_kizeo_pdf

GRAPH = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.Read"]  # permission DÉLÉGUÉE (lit la boîte de l'utilisateur connecté)
CACHE_FILE = "/app/.token_cache.json"


def _save_cache(cache: "msal.SerializableTokenCache") -> None:
    if cache.has_state_changed:
        with open(CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def _build_app() -> "tuple[msal.PublicClientApplication, msal.SerializableTokenCache]":
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cache.deserialize(f.read())
    app = msal.PublicClientApplication(
        client_id=settings.azure_client_id,
        authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}",
        token_cache=cache,
    )
    return app, cache


def get_token(app: "msal.PublicClientApplication") -> str:
    # 1. On tente le cache (jeton déjà obtenu lors d'un précédent lancement).
    for account in app.get_accounts():
        result = app.acquire_token_silent(SCOPES, account=account)
        if result and "access_token" in result:
            print("Jeton récupéré depuis le cache (pas de reconnexion nécessaire).")
            return result["access_token"]

    # 2. Sinon : device-code. Microsoft fournit un message tout prêt (URL + code).
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Échec du device flow : {flow.get('error_description')}")
    print("\n" + "=" * 64)
    print(flow["message"])  # ex. « Pour vous connecter, allez sur … et entrez le code XXXX »
    print("=" * 64 + "\n", flush=True)
    result = app.acquire_token_by_device_flow(flow)  # bloque jusqu'à validation dans le navigateur
    if "access_token" not in result:
        raise RuntimeError(f"Échec de l'authentification : {result.get('error_description')}")
    return result["access_token"]


def main() -> None:
    if not settings.azure_client_id or not settings.azure_tenant_id:
        sys.exit("AZURE_CLIENT_ID / AZURE_TENANT_ID manquants dans .env")

    app, cache = _build_app()
    try:
        token = get_token(app)
    finally:
        _save_cache(cache)

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "$filter": "hasAttachments eq true",
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,receivedDateTime,from,hasAttachments",
        "$top": "25",
    }
    # /me/messages = la boîte de l'utilisateur connecté (flux délégué).
    r = httpx.get(f"{GRAPH}/me/messages", headers=headers, params=params)
    r.raise_for_status()
    messages = r.json().get("value", [])

    kizeo = [
        m for m in messages
        if "kizeo" in (m.get("subject") or "").lower()
        or "etat des lieux" in (m.get("subject") or "").lower()
    ]
    print(f"\n{len(messages)} mail(s) avec pièce jointe, dont {len(kizeo)} Kizeo détecté(s).\n")

    for m in kizeo[:5]:
        print(f"- {m['receivedDateTime']} | {m['subject']}")
        ar = httpx.get(f"{GRAPH}/me/messages/{m['id']}/attachments", headers=headers)
        ar.raise_for_status()
        pdf_trouve = False
        for att in ar.json().get("value", []):
            if att.get("contentType") == "application/pdf":
                pdf_trouve = True
                releve = parse_kizeo_pdf(base64.b64decode(att["contentBytes"]))
                if releve:
                    print(f"    → {releve.site} | {releve.date_releve} | {len(releve.bennes)} benne(s)")
                else:
                    print("    → PDF présent mais non reconnu par le parseur")
                break
        if not pdf_trouve:
            print("    → aucune pièce jointe PDF")

    print("\nTerminé.")


if __name__ == "__main__":
    main()
