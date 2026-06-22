from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.routers.auth import require_admin
from backend import models, schemas

router = APIRouter(prefix="/parametrage", tags=["parametrage"])


@router.get("/seuils", response_model=list[schemas.SeuilAlerteSchema])
def get_seuils(db: Session = Depends(get_db)):
    """Retourne les seuils configurés pour toutes les bennes connues (avec valeurs par défaut si non configurées)."""
    # Toutes les combinaisons (site_id, type_dechet) existantes dans les relevés
    combinaisons = (
        db.query(models.Benne.type_dechet, models.Releve.site_id, models.Site.nom)
        .join(models.Releve, models.Benne.releve_id == models.Releve.id)
        .join(models.Site, models.Releve.site_id == models.Site.id)
        .filter(models.Site.actif == True)
        .distinct()
        .all()
    )

    seuils_config = {
        (s.site_id, s.type_dechet): s
        for s in db.query(models.SeuilAlerte).all()
    }

    result = []
    seen = set()
    for type_dechet, site_id, site_nom in combinaisons:
        key = (site_id, type_dechet)
        if key in seen:
            continue
        seen.add(key)
        cfg = seuils_config.get(key)
        result.append(schemas.SeuilAlerteSchema(
            site_id=site_id,
            site_nom=site_nom,
            type_dechet=type_dechet,
            seuil_avertissement=cfg.seuil_avertissement if cfg else 75,
            seuil_critique=cfg.seuil_critique if cfg else 90,
        ))

    result.sort(key=lambda x: (x.site_nom, x.type_dechet))
    return result


@router.put("/seuils/{site_id}/{type_dechet}", response_model=schemas.SeuilAlerteSchema)
def update_seuil(site_id: int, type_dechet: str, payload: schemas.SeuilAlerteUpdate,
                 _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    """Crée ou met à jour le seuil d'alerte pour une benne donnée (admin)."""
    if payload.seuil_avertissement < 1 or payload.seuil_avertissement > 100:
        raise HTTPException(status_code=422, detail="seuil_avertissement doit être entre 1 et 100")
    if payload.seuil_critique < 1 or payload.seuil_critique > 100:
        raise HTTPException(status_code=422, detail="seuil_critique doit être entre 1 et 100")
    if payload.seuil_avertissement >= payload.seuil_critique:
        raise HTTPException(status_code=422, detail="seuil_avertissement doit être inférieur à seuil_critique")

    site = db.query(models.Site).filter_by(id=site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site introuvable")

    cfg = db.query(models.SeuilAlerte).filter_by(site_id=site_id, type_dechet=type_dechet).first()
    if cfg:
        cfg.seuil_avertissement = payload.seuil_avertissement
        cfg.seuil_critique = payload.seuil_critique
    else:
        cfg = models.SeuilAlerte(
            site_id=site_id,
            type_dechet=type_dechet,
            seuil_avertissement=payload.seuil_avertissement,
            seuil_critique=payload.seuil_critique,
        )
        db.add(cfg)

    db.commit()
    return schemas.SeuilAlerteSchema(
        site_id=site_id,
        site_nom=site.nom,
        type_dechet=type_dechet,
        seuil_avertissement=cfg.seuil_avertissement,
        seuil_critique=cfg.seuil_critique,
    )
