from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas

router = APIRouter(prefix="/bennes", tags=["bennes"])


@router.get("/", response_model=list[schemas.SiteAvecDerniereReleve])
def get_tous_les_sites(db: Session = Depends(get_db)):
    """Retourne l'état actuel de tous les sites actifs avec les taux du dernier relevé."""
    sites = db.query(models.Site).filter_by(actif=True).all()
    result = []
    for site in sites:
        dernier_releve = (
            db.query(models.Releve)
            .filter_by(site_id=site.id)
            .order_by(models.Releve.date_releve.desc(), models.Releve.recu_at.desc())
            .first()
        )
        tassements = {
            t.type_dechet: t.tassee
            for t in db.query(models.Tassement).filter_by(site_id=site.id).all()
        }
        releve_data = None
        if dernier_releve:
            bennes_data = [
                schemas.BenneSchema(
                    id=b.id,
                    type_dechet=b.type_dechet,
                    taux=b.taux,
                    a_compacteur=b.a_compacteur,
                    tassee=tassements.get(b.type_dechet, False),
                )
                for b in dernier_releve.bennes
            ]
            releve_data = schemas.ReleveDetail(
                id=dernier_releve.id,
                date_releve=dernier_releve.date_releve,
                agent=dernier_releve.agent,
                recu_at=dernier_releve.recu_at,
                bennes=bennes_data,
            )
        result.append(schemas.SiteAvecDerniereReleve(
            site=schemas.SiteSchema.model_validate(site),
            releve=releve_data,
        ))
    return result


@router.patch("/{site_id}/tassement", status_code=200)
def mettre_a_jour_tassement(site_id: int, payload: schemas.TassementPayload, db: Session = Depends(get_db)):
    """Marque ou démarque une benne comme tassée."""
    if not db.query(models.Site).filter_by(id=site_id).first():
        raise HTTPException(status_code=404, detail="Site introuvable")
    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=payload.type_dechet).first()
    if t:
        t.tassee = payload.tassee
        if payload.tassee:
            t.tassee_at = datetime.utcnow()
    else:
        t = models.Tassement(
            site_id=site_id,
            type_dechet=payload.type_dechet,
            tassee=payload.tassee,
            tassee_at=datetime.utcnow() if payload.tassee else None,
        )
        db.add(t)
    db.commit()
    return {"tassee": t.tassee}


@router.post("/{site_id}/rotation", status_code=200)
def rotation_benne(site_id: int, payload: schemas.TypeDechetPayload, db: Session = Depends(get_db)):
    """Déclenche une rotation : vide la benne et réinitialise le tassement."""
    if not db.query(models.Site).filter_by(id=site_id).first():
        raise HTTPException(status_code=404, detail="Site introuvable")
    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=payload.type_dechet).first()
    if t:
        t.tassee = False
        t.tassee_at = None
        db.commit()
    return {"rotation": True, "tassee": False}


@router.get("/{site_id}/historique", response_model=list[schemas.ReleveDetail])
def get_historique_site(site_id: int, jours: int = 30, db: Session = Depends(get_db)):
    """Historique des relevés d'un site sur N jours."""
    from datetime import date, timedelta
    depuis = date.today() - timedelta(days=jours)
    return (
        db.query(models.Releve)
        .filter(models.Releve.site_id == site_id, models.Releve.date_releve >= depuis)
        .order_by(models.Releve.date_releve.desc())
        .all()
    )
