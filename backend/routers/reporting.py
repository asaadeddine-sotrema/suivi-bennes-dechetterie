import csv
import io
from collections import defaultdict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models
from backend.services.pdf_parser import est_type_exclu

router = APIRouter(prefix="/reporting", tags=["reporting"])


@router.get("/releves.csv")
def export_releves_csv(jours: int = 365, db: Session = Depends(get_db)):
    """Exporte tous les relevés (une ligne par benne) au format CSV."""
    from datetime import date, timedelta

    depuis = date.today() - timedelta(days=jours)
    releves = (
        db.query(models.Releve)
        .filter(models.Releve.date_releve >= depuis)
        .order_by(models.Releve.date_releve.desc())
        .all()
    )
    sites = {s.id: s for s in db.query(models.Site).all()}

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Date", "Site", "Code", "Agent", "Type de déchet", "Contenant", "Taux (%)"])
    for r in releves:
        site = sites.get(r.site_id)
        for b in r.bennes:
            if est_type_exclu(b.type_dechet):
                continue
            writer.writerow([
                r.date_releve.isoformat(),
                site.nom if site else "",
                site.code if site else "",
                r.agent or "",
                b.type_dechet,
                "Compacteur" if b.a_compacteur else "Benne",
                b.taux,
            ])

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=releves_bennes.csv"},
    )


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Synthèse : par site (relevés, taux moyen, tassements, rotations) + activité mensuelle."""
    sites = db.query(models.Site).filter_by(actif=True).all()

    # Comptage des événements (tassement / rotation) par site et par mois.
    evenements = db.query(models.HistoriqueTassement).all()
    par_site = defaultdict(lambda: {"tassements": 0, "rotations": 0})
    par_mois = defaultdict(lambda: {"tassements": 0, "rotations": 0})
    for ev in evenements:
        cle = "tassements" if ev.evenement == "tassement" else "rotations"
        par_site[ev.site_id][cle] += 1
        if ev.fait_le:
            mois = ev.fait_le.strftime("%Y-%m")
            par_mois[mois][cle] += 1

    lignes = []
    for site in sites:
        dernier = (
            db.query(models.Releve)
            .filter_by(site_id=site.id)
            .order_by(models.Releve.date_releve.desc(), models.Releve.recu_at.desc())
            .first()
        )
        bennes = [b for b in (dernier.bennes if dernier else []) if not est_type_exclu(b.type_dechet)]
        taux_moyen = round(sum(b.taux for b in bennes) / len(bennes)) if bennes else None
        lignes.append({
            "site_id": site.id,
            "site_nom": site.nom,
            "nb_bennes": len(bennes),
            "taux_moyen": taux_moyen,
            "derniere_date": dernier.date_releve.isoformat() if dernier else None,
            "nb_tassements": par_site[site.id]["tassements"],
            "nb_rotations": par_site[site.id]["rotations"],
        })

    activite_mensuelle = [
        {"mois": mois, **valeurs}
        for mois, valeurs in sorted(par_mois.items())
    ]

    return {
        "sites": lignes,
        "activite_mensuelle": activite_mensuelle,
        "totaux": {
            "tassements": sum(l["nb_tassements"] for l in lignes),
            "rotations": sum(l["nb_rotations"] for l in lignes),
        },
    }
