from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas
from backend.services.prevision import prevoir_saturation
from backend.services.pdf_parser import est_type_exclu

router = APIRouter(prefix="/bennes", tags=["bennes"])


def _taux_actuel(db: Session, site_id: int, type_dechet: str) -> int | None:
    """Taux de remplissage de la benne dans le dernier relevé du site (ou None)."""
    dernier = (
        db.query(models.Releve)
        .filter_by(site_id=site_id)
        .order_by(models.Releve.date_releve.desc(), models.Releve.recu_at.desc())
        .first()
    )
    if not dernier:
        return None
    for b in dernier.bennes:
        if b.type_dechet == type_dechet:
            return b.taux
    return None


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
            t.type_dechet: t
            for t in db.query(models.Tassement).filter_by(site_id=site.id).all()
        }
        seuils = {
            s.type_dechet: s
            for s in db.query(models.SeuilAlerte).filter_by(site_id=site.id).all()
        }
        releve_data = None
        if dernier_releve:
            bennes_data = [
                schemas.BenneSchema(
                    id=b.id,
                    type_dechet=b.type_dechet,
                    taux=b.taux,
                    a_compacteur=b.a_compacteur,
                    tassement_demande=tassements[b.type_dechet].tassement_demande if b.type_dechet in tassements else False,
                    tassement_demande_at=tassements[b.type_dechet].tassement_demande_at if b.type_dechet in tassements else None,
                    tassee=tassements[b.type_dechet].tassee if b.type_dechet in tassements else False,
                    tassee_at=tassements[b.type_dechet].tassee_at if b.type_dechet in tassements else None,
                    nb_tassements=tassements[b.type_dechet].nb_tassements if b.type_dechet in tassements else 0,
                    rotation_faite=tassements[b.type_dechet].rotation_faite if b.type_dechet in tassements else False,
                    rotation_faite_at=tassements[b.type_dechet].rotation_faite_at if b.type_dechet in tassements else None,
                    tassement_prevu_at=tassements[b.type_dechet].tassement_prevu_at if b.type_dechet in tassements else None,
                    rotation_prevue_at=tassements[b.type_dechet].rotation_prevue_at if b.type_dechet in tassements else None,
                    seuil_avertissement=seuils[b.type_dechet].seuil_avertissement if b.type_dechet in seuils else 75,
                    seuil_critique=seuils[b.type_dechet].seuil_critique if b.type_dechet in seuils else 90,
                )
                for b in dernier_releve.bennes
                if not est_type_exclu(b.type_dechet)
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


@router.post("/{site_id}/{type_dechet}/planifier-tassement", status_code=200)
def planifier_tassement(site_id: int, type_dechet: str, payload: schemas.PlanifierTassementPayload, db: Session = Depends(get_db)):
    """Planifie un tassement : coupe le circuit d'alertes jusqu'à la date indiquée."""
    if not db.query(models.Site).filter_by(id=site_id).first():
        raise HTTPException(status_code=404, detail="Site introuvable")

    # Normalise en UTC naïf pour rester cohérent avec datetime.utcnow()
    prevu_at = payload.prevu_at
    if prevu_at.tzinfo is not None:
        prevu_at = prevu_at.astimezone(timezone.utc).replace(tzinfo=None)

    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=type_dechet).first()
    if t:
        t.tassement_prevu_at = prevu_at
    else:
        t = models.Tassement(
            site_id=site_id,
            type_dechet=type_dechet,
            tassee=False,
            tassement_prevu_at=prevu_at,
        )
        db.add(t)
    db.commit()
    return {"tassement_prevu_at": t.tassement_prevu_at}


@router.delete("/{site_id}/{type_dechet}/planifier-tassement", status_code=200)
def annuler_planification(site_id: int, type_dechet: str, db: Session = Depends(get_db)):
    """Annule la planification d'un tassement."""
    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=type_dechet).first()
    if t:
        t.tassement_prevu_at = None
        db.commit()
    return {"tassement_prevu_at": None}


@router.post("/{site_id}/{type_dechet}/planifier-rotation", status_code=200)
def planifier_rotation(site_id: int, type_dechet: str, payload: schemas.PlanifierTassementPayload, db: Session = Depends(get_db)):
    """Planifie une rotation : coupe le circuit d'alertes jusqu'à la date indiquée."""
    if not db.query(models.Site).filter_by(id=site_id).first():
        raise HTTPException(status_code=404, detail="Site introuvable")

    # Normalise en UTC naïf pour rester cohérent avec datetime.utcnow()
    prevu_at = payload.prevu_at
    if prevu_at.tzinfo is not None:
        prevu_at = prevu_at.astimezone(timezone.utc).replace(tzinfo=None)

    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=type_dechet).first()
    if t:
        t.rotation_prevue_at = prevu_at
    else:
        t = models.Tassement(
            site_id=site_id,
            type_dechet=type_dechet,
            tassee=False,
            rotation_prevue_at=prevu_at,
        )
        db.add(t)
    db.commit()
    return {"rotation_prevue_at": t.rotation_prevue_at}


@router.delete("/{site_id}/{type_dechet}/planifier-rotation", status_code=200)
def annuler_planification_rotation(site_id: int, type_dechet: str, db: Session = Depends(get_db)):
    """Annule la planification d'une rotation."""
    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=type_dechet).first()
    if t:
        t.rotation_prevue_at = None
        db.commit()
    return {"rotation_prevue_at": None}


@router.get("/{site_id}/tassements/historique", response_model=list[schemas.EvenementTassement])
def get_historique_tassements(site_id: int, type_dechet: str, limite: int = 20, db: Session = Depends(get_db)):
    """Journal des tassements et rotations pour une benne donnée."""
    return (
        db.query(models.HistoriqueTassement)
        .filter_by(site_id=site_id, type_dechet=type_dechet)
        .order_by(models.HistoriqueTassement.fait_le.desc())
        .limit(limite)
        .all()
    )


@router.post("/{site_id}/demander-tassement", status_code=200)
def demander_tassement(site_id: int, payload: schemas.TypeDechetPayload, db: Session = Depends(get_db)):
    """Enregistre une demande de tassement (état intermédiaire).

    La benne ne sera affichée « Tassée » que lorsqu'un relevé montrera un taux
    inférieur au taux de référence enregistré ici (confirmation par les données).
    """
    if not db.query(models.Site).filter_by(id=site_id).first():
        raise HTTPException(status_code=404, detail="Site introuvable")

    now = datetime.utcnow()
    taux_ref = _taux_actuel(db, site_id, payload.type_dechet)
    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=payload.type_dechet).first()
    if t:
        # On conserve l'état « Tassée » et le compteur existants : une benne déjà
        # tassée peut être re-tassée (le compteur s'incrémentera à la confirmation).
        t.tassement_demande = True
        t.tassement_demande_at = now
        t.taux_reference = taux_ref
        # La demande est posée : on lève la planification correspondante.
        t.tassement_prevu_at = None
    else:
        t = models.Tassement(
            site_id=site_id,
            type_dechet=payload.type_dechet,
            tassement_demande=True,
            tassement_demande_at=now,
            taux_reference=taux_ref,
        )
        db.add(t)

    db.add(models.HistoriqueTassement(
        site_id=site_id,
        type_dechet=payload.type_dechet,
        evenement="tassement",
        fait_le=now,
    ))
    db.commit()
    return {"tassement_demande": True, "tassee": t.tassee}


@router.delete("/{site_id}/{type_dechet}/demander-tassement", status_code=200)
def annuler_demande_tassement(site_id: int, type_dechet: str, db: Session = Depends(get_db)):
    """Annule une demande de tassement en attente (avant confirmation)."""
    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=type_dechet).first()
    if t and t.tassement_demande:
        t.tassement_demande = False
        t.tassement_demande_at = None
        t.taux_reference = None
        db.commit()
    return {"tassement_demande": False}


@router.post("/{site_id}/rotation", status_code=200)
def rotation_benne(site_id: int, payload: schemas.TypeDechetPayload, db: Session = Depends(get_db)):
    """Déclenche une rotation : enregistre l'événement et conserve l'état « rotation effectuée »
    tant qu'un relevé ne montre pas un taux inférieur (confirmation physique de la rotation)."""
    if not db.query(models.Site).filter_by(id=site_id).first():
        raise HTTPException(status_code=404, detail="Site introuvable")

    now = datetime.utcnow()
    taux_ref = _taux_actuel(db, site_id, payload.type_dechet)
    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=payload.type_dechet).first()
    if t:
        # La rotation vide la benne : on réinitialise tout état de tassement.
        t.tassement_demande = False
        t.tassement_demande_at = None
        t.tassee = False
        t.tassee_at = None
        t.nb_tassements = 0
        t.rotation_faite = True
        t.rotation_faite_at = now
        t.taux_reference = taux_ref
        # La rotation est faite : on lève toute planification en cours
        t.tassement_prevu_at = None
        t.rotation_prevue_at = None
    else:
        t = models.Tassement(
            site_id=site_id,
            type_dechet=payload.type_dechet,
            tassee=False,
            rotation_faite=True,
            rotation_faite_at=now,
            taux_reference=taux_ref,
        )
        db.add(t)

    db.add(models.HistoriqueTassement(
        site_id=site_id,
        type_dechet=payload.type_dechet,
        evenement="rotation",
        fait_le=now,
    ))
    db.commit()
    return {"rotation": True, "rotation_faite": True}


@router.delete("/{site_id}/{type_dechet}/rotation-faite", status_code=200)
def annuler_rotation_faite(site_id: int, type_dechet: str, db: Session = Depends(get_db)):
    """Retire manuellement l'état « rotation effectuée » d'une benne."""
    t = db.query(models.Tassement).filter_by(site_id=site_id, type_dechet=type_dechet).first()
    if t:
        t.rotation_faite = False
        t.rotation_faite_at = None
        t.taux_reference = None
        db.commit()
    return {"rotation_faite": False}


@router.get("/{site_id}/prevision", response_model=list[schemas.PrevisionSchema])
def get_prevision_site(site_id: int, jours: int = 30, db: Session = Depends(get_db)):
    """Prévision de saturation par benne, à partir de l'historique des N derniers jours."""
    depuis = date.today() - timedelta(days=jours)
    releves = (
        db.query(models.Releve)
        .filter(models.Releve.site_id == site_id, models.Releve.date_releve >= depuis)
        .order_by(models.Releve.date_releve.asc())
        .all()
    )

    seuils = {
        s.type_dechet: s.seuil_critique
        for s in db.query(models.SeuilAlerte).filter_by(site_id=site_id).all()
    }

    # Pivot : une série (date, taux) par type de benne.
    series: dict[str, list[tuple[date, int]]] = {}
    for r in releves:
        for b in r.bennes:
            if est_type_exclu(b.type_dechet):
                continue
            series.setdefault(b.type_dechet, []).append((r.date_releve, b.taux))

    previsions = [
        prevoir_saturation(type_dechet, points, seuils.get(type_dechet, 90))
        for type_dechet, points in series.items()
    ]
    return previsions


@router.get("/{site_id}/historique", response_model=list[schemas.ReleveDetail])
def get_historique_site(site_id: int, jours: int = 30, db: Session = Depends(get_db)):
    """Historique des relevés d'un site sur N jours."""
    depuis = date.today() - timedelta(days=jours)
    return (
        db.query(models.Releve)
        .filter(models.Releve.site_id == site_id, models.Releve.date_releve >= depuis)
        .order_by(models.Releve.date_releve.desc())
        .all()
    )
