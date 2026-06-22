import hashlib
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database import get_db
from backend.services.pdf_parser import parse_kizeo_pdf
from backend.services.alertes import creer_alerte
from backend import models

router = APIRouter(prefix="/upload", tags=["upload"])
logger = logging.getLogger(__name__)


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Dépose un PDF Kizeo Forms, le parse et alimente la base de données.
    Retourne un résumé du relevé importé.
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    pdf_bytes = await file.read()

    # Déduplication : hash SHA-256 du contenu comme identifiant unique
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
    existing = db.query(models.Releve).filter_by(email_message_id=pdf_hash).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Ce fichier a déjà été importé (relevé du {existing.date_releve})",
        )

    releve_data = parse_kizeo_pdf(pdf_bytes)
    if not releve_data:
        raise HTTPException(
            status_code=422,
            detail="PDF non reconnu — vérifiez qu'il s'agit bien d'un formulaire Kizeo 'Etat des lieux des bennes'",
        )

    # Upsert site
    site = db.query(models.Site).filter_by(code=releve_data.site.upper()).first()
    if not site:
        site = models.Site(code=releve_data.site.upper(), nom=releve_data.site)
        db.add(site)
        db.flush()

    # Créer le relevé
    releve = models.Releve(
        site_id=site.id,
        date_releve=releve_data.date_releve,
        agent=releve_data.agent,
        email_message_id=pdf_hash,
    )
    db.add(releve)
    db.flush()

    bennes_alertes = []
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
                creer_alerte(db=db, benne=benne, site=site)
                bennes_alertes.append({"type_dechet": b.type_dechet, "taux": b.taux})

    db.commit()
    logger.info(f"PDF importé : {site.nom} · {releve_data.date_releve} · {len(releve_data.bennes)} bennes")

    return {
        "site": site.nom,
        "code": site.code,
        "date_releve": releve_data.date_releve.isoformat(),
        "agent": releve_data.agent,
        "nb_bennes": len(releve_data.bennes),
        "bennes": [{"type_dechet": b.type_dechet, "taux": b.taux} for b in releve_data.bennes],
        "alertes": bennes_alertes,
    }
