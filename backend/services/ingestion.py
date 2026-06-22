import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.services.graph_watcher import fetch_kizeo_emails, download_pdf_attachment
from backend.services.pdf_parser import parse_kizeo_pdf
from backend.services import alertes as alerte_service
from backend import models
from backend.config import settings

logger = logging.getLogger(__name__)


async def run_sync_pipeline(db: Session) -> dict:
    """
    Pipeline complet :
    1. Polling Graph API pour les nouveaux emails Kizeo
    2. Téléchargement et parsing des PDFs joints
    3. Déduplication par message_id
    4. Persistance en base
    5. Déclenchement des alertes si seuil dépassé
    """
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

            seuil_cfg = db.query(models.SeuilAlerte).filter_by(site_id=site.id, type_dechet=b.type_dechet).first()
            seuil = seuil_cfg.seuil_avertissement if seuil_cfg else settings.alerte_seuil
            if b.taux >= seuil:
                tassement = db.query(models.Tassement).filter_by(site_id=site.id, type_dechet=b.type_dechet).first()
                now = datetime.utcnow()
                if tassement and tassement.tassement_prevu_at and tassement.tassement_prevu_at > now:
                    logger.info(f"Alerte ignorée : tassement planifié le {tassement.tassement_prevu_at} pour {b.type_dechet} ({site.nom})")
                elif tassement and tassement.rotation_prevue_at and tassement.rotation_prevue_at > now:
                    logger.info(f"Alerte ignorée : rotation planifiée le {tassement.rotation_prevue_at} pour {b.type_dechet} ({site.nom})")
                else:
                    await alerte_service.envoyer_alerte(db=db, benne=benne, site=site)
                    stats["alertes"] += 1

        db.commit()
        stats["traites"] += 1
        logger.info(f"Relevé persisté : {site.nom} · {releve_data.date_releve}")

    return stats
