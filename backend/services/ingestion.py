import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.services.graph_watcher import fetch_kizeo_emails, download_pdf_attachment
from backend.services.pdf_parser import parse_kizeo_pdf
from backend.services import alertes as alerte_service
from backend import models
from backend.config import settings

logger = logging.getLogger(__name__)


def appliquer_baisse_taux(tassement, taux_releve: int) -> bool:
    """Applique l'effet d'un relevé montrant un taux inférieur à la référence enregistrée.

    - Demande de tassement en attente -> confirmée : la benne devient « Tassée ».
    - Rotation en attente -> confirmée : l'indicateur est retiré.

    Retourne True si un changement a effectivement eu lieu.
    """
    if not tassement or tassement.taux_reference is None or taux_releve >= tassement.taux_reference:
        return False

    if tassement.tassement_demande:
        # La baisse de taux confirme le tassement demandé (une benne peut être
        # tassée plusieurs fois : on incrémente le compteur).
        tassement.tassement_demande = False
        tassement.tassement_demande_at = None
        tassement.tassee = True
        tassement.tassee_at = datetime.utcnow()
        tassement.nb_tassements = (tassement.nb_tassements or 0) + 1
        tassement.taux_reference = None
        return True

    if tassement.rotation_faite:
        # La baisse de taux confirme la rotation : on retire l'indicateur.
        tassement.rotation_faite = False
        tassement.rotation_faite_at = None
        tassement.taux_reference = None
        return True

    return False


async def run_sync_pipeline(db: Session) -> dict:
    """
    Pipeline complet :
    1. Polling Graph API pour les nouveaux emails Kizeo
    2. Téléchargement et parsing des PDFs joints
    3. Déduplication par message_id
    4. Persistance en base
    5. Déclenchement des alertes si seuil dépassé
    """
    if not settings.sync_configure:
        raise RuntimeError(
            "Synchronisation Kizeo non configurée : renseignez AZURE_TENANT_ID, "
            "AZURE_CLIENT_ID, AZURE_CLIENT_SECRET et OUTLOOK_USER_EMAIL."
        )

    since = datetime.utcnow() - timedelta(hours=24)
    emails = await fetch_kizeo_emails(since=since)

    stats = {"traites": 0, "ignores": 0, "erreurs": 0, "alertes": 0}

    for email in emails:
        message_id = email["id"]

        existing = db.query(models.Releve).filter_by(email_message_id=message_id).first()
        if existing:
            stats["ignores"] += 1
            continue

        pdf_bytes = await download_pdf_attachment(message_id)
        if not pdf_bytes:
            logger.warning(f"Pas de PDF pour le message {message_id}")
            stats["erreurs"] += 1
            continue

        releve_data = parse_kizeo_pdf(pdf_bytes)
        if not releve_data:
            stats["erreurs"] += 1
            continue

        site = db.query(models.Site).filter_by(code=releve_data.site.upper()).first()
        if not site:
            site = models.Site(code=releve_data.site.upper(), nom=releve_data.site)
            db.add(site)
            db.flush()

        releve = models.Releve(
            site_id=site.id,
            date_releve=releve_data.date_releve,
            agent=releve_data.agent,
            email_message_id=message_id,
        )
        db.add(releve)
        db.flush()

        for b in releve_data.bennes:
            benne = models.Benne(
                releve_id=releve.id,
                type_dechet=b.type_dechet,
                taux=b.taux,
                a_compacteur=b.a_compacteur,
            )
            db.add(benne)
            db.flush()

            tassement = db.query(models.Tassement).filter_by(site_id=site.id, type_dechet=b.type_dechet).first()

            # Un taux inférieur à la référence confirme le tassement (-> « Tassée »)
            # ou la rotation (-> indicateur retiré).
            if appliquer_baisse_taux(tassement, b.taux):
                logger.info(f"État tassement/rotation mis à jour : taux {b.taux}% < référence pour {b.type_dechet} ({site.nom})")

            seuil_cfg = db.query(models.SeuilAlerte).filter_by(site_id=site.id, type_dechet=b.type_dechet).first()
            seuil = seuil_cfg.seuil_avertissement if seuil_cfg else settings.alerte_seuil
            if b.taux >= seuil:
                now = datetime.utcnow()
                if tassement and tassement.tassement_prevu_at and tassement.tassement_prevu_at > now:
                    logger.info(f"Alerte ignorée : tassement planifié le {tassement.tassement_prevu_at} pour {b.type_dechet} ({site.nom})")
                elif tassement and tassement.rotation_prevue_at and tassement.rotation_prevue_at > now:
                    logger.info(f"Alerte ignorée : rotation planifiée le {tassement.rotation_prevue_at} pour {b.type_dechet} ({site.nom})")
                else:
                    alerte_service.creer_alerte(db=db, benne=benne, site=site)
                    stats["alertes"] += 1

        db.commit()
        stats["traites"] += 1
        logger.info(f"Relevé persisté : {site.nom} · {releve_data.date_releve}")

    return stats
