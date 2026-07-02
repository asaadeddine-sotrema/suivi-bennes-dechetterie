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
    alerte = alerte_service.enregistrer_alerte(db, benne, site, seuil=75)
    alerte_service.envoyer_alertes_groupees(db, [(alerte, site.nom, benne.type_dechet, benne.taux)])
    db.flush()
    a = db.query(models.Alerte).filter_by(benne_id=benne.id).first()
    assert a is not None
    assert a.statut == "enregistre"
    assert a.email_destinataire is None


def test_alerte_avec_envoi_email(db, benne_site, monkeypatch):
    monkeypatch.setattr(settings, "alerte_destinataires", "expl@sotrema.fr")
    monkeypatch.setattr(alerte_service, "envoyer_email", lambda **kw: True)
    benne, site = benne_site
    alerte = alerte_service.enregistrer_alerte(db, benne, site, seuil=75)
    alerte_service.envoyer_alertes_groupees(db, [(alerte, site.nom, benne.type_dechet, benne.taux)])
    db.flush()
    a = db.query(models.Alerte).filter_by(benne_id=benne.id).first()
    assert a.statut == "envoye"
    assert a.email_destinataire == "expl@sotrema.fr"


def test_un_seul_email_pour_plusieurs_bennes(db, benne_site, monkeypatch):
    """Plusieurs bennes en dépassement -> un unique appel à envoyer_email."""
    monkeypatch.setattr(settings, "alerte_destinataires", "expl@sotrema.fr")
    appels = []
    monkeypatch.setattr(alerte_service, "envoyer_email", lambda **kw: appels.append(kw) or True)
    base_benne, site = benne_site
    b1 = models.Benne(releve_id=base_benne.releve_id, type_dechet="Ferraille", taux=88, a_compacteur=False)
    b2 = models.Benne(releve_id=base_benne.releve_id, type_dechet="Gravats", taux=95, a_compacteur=False)
    db.add_all([b1, b2])
    db.flush()
    a1 = alerte_service.enregistrer_alerte(db, b1, site, seuil=75)
    a2 = alerte_service.enregistrer_alerte(db, b2, site, seuil=75)
    alerte_service.envoyer_alertes_groupees(
        db, [(a1, site.nom, b1.type_dechet, b1.taux), (a2, site.nom, b2.type_dechet, b2.taux)]
    )
    assert len(appels) == 1  # un seul email pour les deux bennes d'un même site
    assert "Ferraille" in appels[0]["corps"] and "Gravats" in appels[0]["corps"]


def test_un_mail_par_dechetterie(db, monkeypatch):
    """Deux sites en dépassement -> deux emails distincts (un par déchèterie)."""
    monkeypatch.setattr(settings, "alerte_destinataires", "expl@sotrema.fr")
    appels = []
    monkeypatch.setattr(alerte_service, "envoyer_email", lambda **kw: appels.append(kw) or True)

    items = []
    for code, nom in [("LIMAY", "Limay"), ("EPONE", "Épône")]:
        site = models.Site(code=code, nom=nom, actif=True)
        db.add(site)
        db.flush()
        releve = models.Releve(site_id=site.id, date_releve=date(2026, 6, 20))
        db.add(releve)
        db.flush()
        benne = models.Benne(releve_id=releve.id, type_dechet="Bois", taux=90, a_compacteur=False)
        db.add(benne)
        db.flush()
        alerte = alerte_service.enregistrer_alerte(db, benne, site, seuil=75)
        items.append((alerte, site.nom, benne.type_dechet, benne.taux))

    alerte_service.envoyer_alertes_groupees(db, items)
    assert len(appels) == 2  # un email par site
    sujets = sorted(a["sujet"] for a in appels)
    assert "Limay" in sujets[0] and "Épône" in sujets[1]


def test_envoyer_email_non_configure_retourne_false(monkeypatch):
    from backend.services.email import envoyer_email
    # Ni Graph ni SMTP configurés : l'envoi doit être ignoré (sans appel réseau).
    monkeypatch.setattr(settings, "azure_tenant_id", "")
    monkeypatch.setattr(settings, "azure_client_id", "")
    monkeypatch.setattr(settings, "azure_client_secret", "")
    monkeypatch.setattr(settings, "outlook_user_email", "")
    monkeypatch.setattr(settings, "smtp_host", "")
    assert envoyer_email("sujet", "corps", ["x@y.fr"]) is False
