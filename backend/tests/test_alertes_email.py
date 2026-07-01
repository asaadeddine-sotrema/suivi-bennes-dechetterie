"""Tests de la création d'alerte et de l'envoi d'email associé."""
from datetime import date

import pytest

from backend import models
from backend.config import settings
from backend.services import alertes as alerte_service


@pytest.fixture
def benne_site(db):
    site = models.Site(code="LIMAY", nom="Limay", actif=True)
    db.add(site)
    db.flush()
    releve = models.Releve(site_id=site.id, date_releve=date(2026, 6, 20))
    db.add(releve)
    db.flush()
    benne = models.Benne(releve_id=releve.id, type_dechet="Bois", taux=92, a_compacteur=False)
    db.add(benne)
    db.flush()
    return benne, site


def test_alerte_sans_smtp_est_enregistree(db, benne_site, monkeypatch):
    monkeypatch.setattr(settings, "alerte_destinataires", "")
    benne, site = benne_site
    alerte_service.creer_alerte(db, benne, site)
    db.flush()
    a = db.query(models.Alerte).filter_by(benne_id=benne.id).first()
    assert a is not None
    assert a.statut == "enregistre"
    assert a.email_destinataire is None


def test_alerte_avec_envoi_email(db, benne_site, monkeypatch):
    monkeypatch.setattr(settings, "alerte_destinataires", "expl@sotrema.fr")
    monkeypatch.setattr(alerte_service, "envoyer_email", lambda **kw: True)
    benne, site = benne_site
    alerte_service.creer_alerte(db, benne, site)
    db.flush()
    a = db.query(models.Alerte).filter_by(benne_id=benne.id).first()
    assert a.statut == "envoye"
    assert a.email_destinataire == "expl@sotrema.fr"


def test_envoyer_email_non_configure_retourne_false(monkeypatch):
    from backend.services.email import envoyer_email
    monkeypatch.setattr(settings, "smtp_host", "")
    assert envoyer_email("sujet", "corps", ["x@y.fr"]) is False
