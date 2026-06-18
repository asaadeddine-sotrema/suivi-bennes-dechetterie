from fastapi import APIRouter, Depends
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
            .order_by(models.Releve.date_releve.desc())
            .first()
        )
        result.append(schemas.SiteAvecDerniereReleve(
            site=site,
            releve=dernier_releve,
        ))
    return result


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
