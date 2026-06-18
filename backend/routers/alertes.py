from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas

router = APIRouter(prefix="/alertes", tags=["alertes"])


@router.get("/actives", response_model=list[schemas.AlerteSchema])
def get_alertes_actives(db: Session = Depends(get_db)):
    """Retourne les alertes dont le statut est 'envoye' (non résolues)."""
    return db.query(models.Alerte).filter_by(statut="envoye").order_by(models.Alerte.envoye_at.desc()).all()


@router.get("/", response_model=list[schemas.AlerteSchema])
def get_toutes_alertes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Historique complet des alertes envoyées."""
    return (
        db.query(models.Alerte)
        .order_by(models.Alerte.envoye_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


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
