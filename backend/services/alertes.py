import logging
from sqlalchemy.orm import Session
from backend import models

logger = logging.getLogger(__name__)


def creer_alerte(db: Session, benne: models.Benne, site: models.Site) -> None:
    """Persiste une alerte en base (pas d'envoi email en mode démo)."""

    existing = db.query(models.Alerte).filter_by(benne_id=benne.id).first()
    if existing:
        return

    alerte = models.Alerte(
        benne_id=benne.id,
        seuil_declenche=benne.taux,
        email_destinataire=None,
        statut="envoye",
    )
    db.add(alerte)
    logger.info(f"Alerte créée : {benne.type_dechet} · {site.nom} ({benne.taux}%)")
