from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload, contains_eager
from backend.database import get_db
from backend import models, schemas

router = APIRouter(prefix="/alertes", tags=["alertes"])


def _enrichir(alertes: list[models.Alerte]) -> list[dict]:
    result = []
    for a in alertes:
        d = {c.name: getattr(a, c.name) for c in a.__table__.columns}
        d["type_dechet"] = a.benne.type_dechet if a.benne else None
        d["site_nom"] = a.benne.releve.site.nom if a.benne and a.benne.releve and a.benne.releve.site else None
        result.append(d)
    return result


def _query_alertes(db: Session):
    return (
        db.query(models.Alerte)
        .options(
            joinedload(models.Alerte.benne)
            .joinedload(models.Benne.releve)
            .joinedload(models.Releve.site)
        )
    )


@router.get("/actives", response_model=list[schemas.AlerteSchema])
def get_alertes_actives(db: Session = Depends(get_db)):
    """Retourne les alertes dont le statut est 'envoye' (non résolues)."""
    alertes = _query_alertes(db).filter_by(statut="envoye").order_by(models.Alerte.envoye_at.desc()).all()
    return _enrichir(alertes)


@router.get("/", response_model=list[schemas.AlerteSchema])
def get_toutes_alertes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Historique complet des alertes envoyées."""
    alertes = _query_alertes(db).order_by(models.Alerte.envoye_at.desc()).offset(skip).limit(limit).all()
    return _enrichir(alertes)


@router.patch("/{alerte_id}/resoudre", response_model=schemas.AlerteSchema)
def resoudre_alerte(alerte_id: int, db: Session = Depends(get_db)):
    """Marque une alerte comme résolue."""
    from fastapi import HTTPException
    alerte = db.query(models.Alerte).filter_by(id=alerte_id).first()
    if not alerte:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    alerte.statut = "resolu"
    db.commit()
    db.refresh(alerte)
    return alerte
