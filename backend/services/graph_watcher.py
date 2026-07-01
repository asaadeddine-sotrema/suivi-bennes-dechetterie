import msal
import httpx
import logging
from datetime import datetime, timedelta, timezone
from backend.config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/.default"]


def _graph_datetime(dt: datetime) -> str:
    """Formate un datetime pour un $filter Graph : toujours UTC, suffixe 'Z' unique.

    Gère les datetimes naïfs (supposés UTC) comme aware (convertis en UTC), pour
    éviter un littéral invalide type '...+00:00Z'.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


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

    # On filtre côté serveur uniquement sur la date (même propriété que $orderby) :
    # combiner hasAttachments dans $filter avec un $orderby sur receivedDateTime
    # fait rejeter la requête par Graph (400 "restriction or sort order too complex").
    # La présence de pièce jointe est vérifiée côté code via hasAttachments.
    params = {
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,receivedDateTime,from,hasAttachments",
        "$top": "50",
    }
    if since:
        params["$filter"] = f"receivedDateTime ge {_graph_datetime(since)}"

    url = f"{GRAPH_BASE}/users/{settings.outlook_user_email}/messages"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        messages = resp.json().get("value", [])

    kizeo_msgs = [
        m for m in messages
        if m.get("hasAttachments")
    ]

    logger.info(f"{len(kizeo_msgs)} email(s) Kizeo détecté(s)")
    return kizeo_msgs


def send_mail_graph(subject: str, body: str, recipients: list[str]) -> bool:
    """Envoie un email via Microsoft Graph (sendMail) depuis la boîte configurée.

    Synchrone (msal + httpx.Client) pour être appelé depuis le code métier. Requiert
    la permission applicative Mail.Send (+ consentement admin). Best-effort : en cas
    d'échec on journalise et on renvoie False sans lever d'exception.
    """
    if not recipients:
        return False
    try:
        token = get_access_token()
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": r}} for r in recipients],
            },
            "saveToSentItems": True,
        }
        url = f"{GRAPH_BASE}/users/{settings.outlook_user_email}/sendMail"
        with httpx.Client() as client:
            resp = client.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)
            resp.raise_for_status()
        logger.info(f"Email d'alerte envoyé via Graph à {', '.join(recipients)}")
        return True
    except Exception as e:  # noqa: BLE001 — best-effort, on ne casse pas le métier
        logger.error(f"Échec de l'envoi de l'email d'alerte via Graph : {e}")
        return False


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
