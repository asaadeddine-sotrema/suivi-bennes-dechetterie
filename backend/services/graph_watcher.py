import msal
import httpx
import logging
from datetime import datetime, timedelta
from backend.config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/.default"]


def get_access_token() -> str:
    app = msal.ConfidentialClientApplication(
        client_id=settings.azure_client_id,
        client_credential=settings.azure_client_secret,
        authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}",
    )
    result = app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" not in result:
        raise RuntimeError(f"Échec authentification Graph API : {result.get('error_description')}")
    return result["access_token"]


async def fetch_kizeo_emails(since: datetime | None = None) -> list[dict]:
    """
    Récupère les emails contenant un PDF Kizeo Forms.
    Filtre sur l'objet et la présence d'une pièce jointe PDF.
    """
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    filter_parts = ["hasAttachments eq true"]
    if since:
        filter_parts.append(f"receivedDateTime ge {since.isoformat()}Z")

    params = {
        "$filter": " and ".join(filter_parts),
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,receivedDateTime,from,hasAttachments",
        "$top": "50",
    }

    url = f"{GRAPH_BASE}/users/{settings.outlook_user_email}/messages"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        messages = resp.json().get("value", [])

    kizeo_msgs = [
        m for m in messages
        if "kizeo" in m.get("subject", "").lower()
        or "etat des lieux" in m.get("subject", "").lower()
    ]

    logger.info(f"{len(kizeo_msgs)} email(s) Kizeo détecté(s)")
    return kizeo_msgs


async def download_pdf_attachment(message_id: str) -> bytes | None:
    """Télécharge la première pièce jointe PDF d'un message."""
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/users/{settings.outlook_user_email}/messages/{message_id}/attachments"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        attachments = resp.json().get("value", [])

    for att in attachments:
        if att.get("contentType") == "application/pdf":
            import base64
            return base64.b64decode(att["contentBytes"])

    return None
