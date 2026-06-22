"""Tests du coupe-circuit d'alerte (le cœur de la logique métier).

On importe un PDF via la route /upload/pdf en remplaçant le parseur par un faux
relevé, puis on vérifie quand une alerte est créée ou supprimée.
"""
from datetime import date, datetime, timedelta

import pytest

from backend import models
from backend.services.pdf_parser import ReleveData, BenneData


def _faux_releve(taux=95, type_dechet="Bois"):
    return ReleveData(
        site="Limay",
        agent="Test",
        date_releve=date(2026, 6, 20),
        bennes=[BenneData(type_dechet=type_dechet, taux=taux, a_compacteur=False)],
    )


@pytest.fixture
def patch_parser(monkeypatch):
    """Remplace le parseur PDF par une fonction renvoyant un relevé contrôlé."""
    def _install(releve):
        monkeypatch.setattr("backend.routers.upload.parse_kizeo_pdf", lambda _bytes: releve)
    return _install


def _upload(client, contenu):
    # Un contenu unique évite le rejet pour doublon (hash SHA-256).
    return client.post(
        "/upload/pdf",
        files={"file": (f"r-{contenu}.pdf", contenu.encode(), "application/pdf")},
    )


def test_alerte_creee_au_dessus_du_seuil(client, patch_parser):
    patch_parser(_faux_releve(taux=95))
    resp = _upload(client, "cas-a")
    assert resp.status_code == 200
    assert len(resp.json()["alertes"]) == 1


def test_pas_d_alerte_sous_le_seuil(client, patch_parser):
    patch_parser(_faux_releve(taux=50))
    resp = _upload(client, "cas-sous-seuil")
    assert resp.status_code == 200
    assert resp.json()["alertes"] == []


def _preparer_planification(db, champ, quand):
    """Crée le site et une planification (tassement ou rotation) sur la benne Bois."""
    site = models.Site(code="LIMAY", nom="Limay", actif=True)
    db.add(site)
    db.flush()
    t = models.Tassement(site_id=site.id, type_dechet="Bois", tassee=False)
    setattr(t, champ, quand)
    db.add(t)
    db.commit()


def test_tassement_planifie_futur_supprime_l_alerte(client, patch_parser, db):
    _preparer_planification(db, "tassement_prevu_at", datetime.utcnow() + timedelta(hours=6))
    patch_parser(_faux_releve(taux=95))
    resp = _upload(client, "cas-tassement-futur")
    assert resp.status_code == 200
    assert resp.json()["alertes"] == []  # coupe-circuit actif


def test_rotation_planifiee_futur_supprime_l_alerte(client, patch_parser, db):
    _preparer_planification(db, "rotation_prevue_at", datetime.utcnow() + timedelta(hours=6))
    patch_parser(_faux_releve(taux=95))
    resp = _upload(client, "cas-rotation-futur")
    assert resp.status_code == 200
    assert resp.json()["alertes"] == []


def test_planification_passee_n_empeche_pas_l_alerte(client, patch_parser, db):
    _preparer_planification(db, "tassement_prevu_at", datetime.utcnow() - timedelta(hours=1))
    patch_parser(_faux_releve(taux=95))
    resp = _upload(client, "cas-tassement-passe")
    assert resp.status_code == 200
    assert len(resp.json()["alertes"]) == 1  # planification expirée : alerte rétablie


def test_doublon_rejete(client, patch_parser):
    patch_parser(_faux_releve(taux=95))
    assert _upload(client, "meme-contenu").status_code == 200
    assert _upload(client, "meme-contenu").status_code == 409
