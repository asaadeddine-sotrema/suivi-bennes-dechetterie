"""Envoi d'emails d'alerte par SMTP (best-effort).

Le module est volontairement tolérant : si le SMTP n'est pas configuré, l'envoi
est simplement ignoré (mode démo). En cas d'erreur réseau, on journalise sans
faire échouer le traitement métier (l'alerte reste enregistrée en base).
"""
import logging
import smtplib
from email.message import EmailMessage

from backend.config import settings

logger = logging.getLogger(__name__)


def envoyer_email(sujet: str, corps: str, destinataires: list[str] | None = None) -> bool:
    """Envoie un email d'alerte. Retourne True si l'envoi a réussi.

    Transport privilégié : Microsoft Graph (sendMail) si l'app Azure est configurée.
    À défaut, SMTP. Sinon, mode démo (aucun envoi).
    """
    dests = destinataires or settings.destinataires_alerte
    if not dests:
        return False

    if settings.sync_configure:
        from backend.services.graph_watcher import send_mail_graph
        return send_mail_graph(sujet, corps, dests)

    if not settings.smtp_configure:
        logger.info("Aucun transport mail configuré : email d'alerte ignoré (mode démo).")
        return False

    msg = EmailMessage()
    msg["Subject"] = sujet
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(dests)
    msg.set_content(corps)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as serveur:
            if settings.smtp_tls:
                serveur.starttls()
            if settings.smtp_user:
                serveur.login(settings.smtp_user, settings.smtp_password)
            serveur.send_message(msg)
        logger.info(f"Email d'alerte envoyé à {', '.join(dests)}")
        return True
    except Exception as e:  # noqa: BLE001 — best-effort, on ne casse pas le métier
        logger.error(f"Échec de l'envoi de l'email d'alerte : {e}")
        return False
