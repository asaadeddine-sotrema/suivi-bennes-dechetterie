"""Tests de l'import manuel de PDF, et de son effet sur l'état tassement/rotation."""
from datetime import date

from backend import models
from backend.services.pdf_parser import ReleveData, BenneData


def _site_avec_demande_de_tassement(db, taux_initial=80):
    """Site + relevé à `taux_initial`% + une demande de tassement (référence = taux_initial)."""
    site = models.Site(code="LIMAY", nom="Limay", actif=True)
    db.add(site)
    db.flush()
    releve = models.Releve(site_id=site.id, date_releve=date(2026, 6, 24), agent="Test")
    db.add(releve)
    db.flush()
    db.add(models.Benne(releve_id=releve.id, type_dechet="Bois", taux=taux_initial, a_compacteur=False))
    db.add(models.Tassement(
        site_id=site.id, type_dechet="Bois",
        tassement_demande=True, taux_reference=taux_initial,
    ))
    db.commit()
    return site


def test_import_pdf_en_baisse_confirme_la_tassee(client, db, monkeypatch):
    site = _site_avec_demande_de_tassement(db, taux_initial=80)

    # Le parseur renvoie un relevé en baisse (15% < référence 80%).
    faux_releve = ReleveData(
        site="limay", agent="Test", date_releve=date(2026, 6, 25),
        bennes=[BenneData(type_dechet="Bois", taux=15, a_compacteur=False)],
    )
    monkeypatch.setattr("backend.routers.upload.parse_kizeo_pdf", lambda _: faux_releve)

    resp = client.post(
        "/upload/pdf",
        files={"file": ("releve.pdf", b"%PDF-fake", "application/pdf")},
    )
    assert resp.status_code == 200

    t = db.query(models.Tassement).filter_by(site_id=site.id, type_dechet="Bois").first()
    db.refresh(t)
    assert t.tassement_demande is False
    assert t.tassee is True
    assert t.taux_reference is None


def test_import_pdf_sans_baisse_conserve_la_demande(client, db, monkeypatch):
    site = _site_avec_demande_de_tassement(db, taux_initial=80)

    # Taux stable (85% >= référence) : la demande reste en attente.
    faux_releve = ReleveData(
        site="limay", agent="Test", date_releve=date(2026, 6, 25),
        bennes=[BenneData(type_dechet="Bois", taux=85, a_compacteur=False)],
    )
    monkeypatch.setattr("backend.routers.upload.parse_kizeo_pdf", lambda _: faux_releve)

    resp = client.post(
        "/upload/pdf",
        files={"file": ("releve.pdf", b"%PDF-fake-2", "application/pdf")},
    )
    assert resp.status_code == 200

    t = db.query(models.Tassement).filter_by(site_id=site.id, type_dechet="Bois").first()
    db.refresh(t)
    assert t.tassement_demande is True
    assert t.tassee is False
