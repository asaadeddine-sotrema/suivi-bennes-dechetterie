import logging
from sqlalchemy.orm import Session
from backend import models
from backend.config import settings
from backend.services.email import envoyer_email

logger = logging.getLogger(__name__)


def creer_alerte(db: Session, benne: models.Benne, site: models.Site) -> None:
    """Persiste une alerte en base et envoie un email aux destinataires (si configuré)."""

    existing = db.query(models.Alerte).filter_by(benne_id=benne.id).first()
    if existing:
        return

    destinataires = settings.destinataires_alerte
    envoye = False
    if destinataires:
        envoye = envoyer_email(
            sujet=f"[Bennes] Seuil atteint : {benne.type_dechet} · {site.nom} ({benne.taux}%)",
            corps=(
                f"La benne « {benne.type_dechet} » de la déchetterie {site.nom} "
                f"a atteint {benne.taux}% de remplissage.\n\n"
                "Pensez à planifier un tassement ou une rotation."
            ),
            destinataires=destinataires,
        )

    alerte = models.Alerte(
        benne_id=benne.id,
        seuil_declenche=benne.taux,
        email_destinataire=", ".join(destinataires) if destinataires else None,
        statut="envoye" if envoye else "enregistre",
    )
    db.add(alerte)
    logger.info(f"Alerte créée : {benne.type_dechet} · {site.nom} ({benne.taux}%) · email={envoye}")
