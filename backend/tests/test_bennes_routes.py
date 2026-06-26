"""Tests des routes de planification et d'état des bennes."""
from datetime import date, datetime, timedelta

import pytest

from backend import models


@pytest.fixture
def site_avec_benne(db):
    """Crée un site avec un relevé et une benne 'Bois' à 80%."""
    site = models.Site(code="LIMAY", nom="Limay", actif=True)
    db.add(site)
    db.flush()
    releve = models.Releve(site_id=site.id, date_releve=date(2026, 6, 20), agent="Test")
    db.add(releve)
    db.flush()
    benne = models.Benne(releve_id=releve.id, type_dechet="Bois", taux=80, a_compacteur=False)
    db.add(benne)
    db.commit()
    return site


def test_get_bennes_renvoie_seuils_par_defaut(client, site_avec_benne):
    resp = client.get("/bennes/")
    assert resp.status_code == 200
    data = resp.json()
    benne = data[0]["releve"]["bennes"][0]
    assert benne["type_dechet"] == "Bois"
    assert benne["seuil_avertissement"] == 75
    assert benne["seuil_critique"] == 90
    assert benne["tassement_prevu_at"] is None
    assert benne["rotation_prevue_at"] is None


def test_planifier_tassement_cree_et_renvoie_date(client, site_avec_benne):
    futur = (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z"
    resp = client.post(f"/bennes/{site_avec_benne.id}/Bois/planifier-tassement", json={"prevu_at": futur})
    assert resp.status_code == 200
    assert resp.json()["tassement_prevu_at"] is not None


def test_planifier_tassement_site_inconnu(client):
    futur = (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z"
    resp = client.post("/bennes/999/Bois/planifier-tassement", json={"prevu_at": futur})
    assert resp.status_code == 404


def test_annuler_tassement(client, site_avec_benne, db):
    futur = (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z"
    client.post(f"/bennes/{site_avec_benne.id}/Bois/planifier-tassement", json={"prevu_at": futur})
    resp = client.delete(f"/bennes/{site_avec_benne.id}/Bois/planifier-tassement")
    assert resp.status_code == 200
    assert resp.json()["tassement_prevu_at"] is None
    t = db.query(models.Tassement).filter_by(site_id=site_avec_benne.id, type_dechet="Bois").first()
    assert t.tassement_prevu_at is None


def test_planifier_rotation_et_annuler(client, site_avec_benne, db):
    futur = (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z"
    resp = client.post(f"/bennes/{site_avec_benne.id}/Bois/planifier-rotation", json={"prevu_at": futur})
    assert resp.status_code == 200
    assert resp.json()["rotation_prevue_at"] is not None

    resp = client.delete(f"/bennes/{site_avec_benne.id}/Bois/planifier-rotation")
    assert resp.json()["rotation_prevue_at"] is None


def test_tassement_aware_normalise_en_utc_naif(client, site_avec_benne, db):
    # 12:00 en UTC+2 doit être stocké comme 10:00 UTC naïf.
    resp = client.post(
        f"/bennes/{site_avec_benne.id}/Bois/planifier-tassement",
        json={"prevu_at": "2099-06-22T12:00:00+02:00"},
    )
    assert resp.status_code == 200
    t = db.query(models.Tassement).filter_by(site_id=site_avec_benne.id, type_dechet="Bois").first()
    assert t.tassement_prevu_at.tzinfo is None
    assert t.tassement_prevu_at.hour == 10


def test_demande_tassement_leve_la_planification(client, site_avec_benne, db):
    futur = (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z"
    client.post(f"/bennes/{site_avec_benne.id}/Bois/planifier-tassement", json={"prevu_at": futur})

    resp = client.post(f"/bennes/{site_avec_benne.id}/demander-tassement", json={"type_dechet": "Bois"})
    assert resp.status_code == 200
    assert resp.json()["tassement_demande"] is True
    assert resp.json()["tassee"] is False  # pas encore confirmé par les données

    t = db.query(models.Tassement).filter_by(site_id=site_avec_benne.id, type_dechet="Bois").first()
    assert t.tassement_demande is True
    assert t.tassee is False
    assert t.tassement_prevu_at is None  # planification levée par la demande


def test_rotation_reinitialise_etat_et_journalise(client, site_avec_benne, db):
    # On demande un tassement, on planifie une rotation, puis on effectue la rotation.
    client.post(f"/bennes/{site_avec_benne.id}/demander-tassement", json={"type_dechet": "Bois"})
    futur = (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z"
    client.post(f"/bennes/{site_avec_benne.id}/Bois/planifier-rotation", json={"prevu_at": futur})

    resp = client.post(f"/bennes/{site_avec_benne.id}/rotation", json={"type_dechet": "Bois"})
    assert resp.status_code == 200

    t = db.query(models.Tassement).filter_by(site_id=site_avec_benne.id, type_dechet="Bois").first()
    assert t.tassement_demande is False
    assert t.tassee is False
    assert t.tassement_prevu_at is None
    assert t.rotation_prevue_at is None

    # Un événement 'rotation' doit être journalisé.
    resp = client.get(f"/bennes/{site_avec_benne.id}/tassements/historique", params={"type_dechet": "Bois"})
    evenements = [e["evenement"] for e in resp.json()]
    assert "rotation" in evenements


def test_demande_tassement_enregistre_reference(client, site_avec_benne, db):
    # La benne est à 80% : la demande fixe la référence à 80, sans confirmer la tassée.
    resp = client.post(f"/bennes/{site_avec_benne.id}/demander-tassement", json={"type_dechet": "Bois"})
    assert resp.json()["tassement_demande"] is True
    t = db.query(models.Tassement).filter_by(site_id=site_avec_benne.id, type_dechet="Bois").first()
    assert t.taux_reference == 80
    assert t.tassement_demande is True
    assert t.tassee is False

    # L'état est exposé dans /bennes/ et le taux reste affiché.
    benne = client.get("/bennes/").json()[0]["releve"]["bennes"][0]
    assert benne["tassement_demande"] is True
    assert benne["tassee"] is False
    assert benne["taux"] == 80


def test_annuler_demande_tassement(client, site_avec_benne, db):
    client.post(f"/bennes/{site_avec_benne.id}/demander-tassement", json={"type_dechet": "Bois"})
    resp = client.delete(f"/bennes/{site_avec_benne.id}/Bois/demander-tassement")
    assert resp.status_code == 200
    assert resp.json()["tassement_demande"] is False

    t = db.query(models.Tassement).filter_by(site_id=site_avec_benne.id, type_dechet="Bois").first()
    assert t.tassement_demande is False
    assert t.taux_reference is None


def test_rotation_pose_etat_persistant(client, site_avec_benne, db):
    resp = client.post(f"/bennes/{site_avec_benne.id}/rotation", json={"type_dechet": "Bois"})
    assert resp.json()["rotation_faite"] is True

    t = db.query(models.Tassement).filter_by(site_id=site_avec_benne.id, type_dechet="Bois").first()
    assert t.rotation_faite is True
    assert t.rotation_faite_at is not None
    assert t.taux_reference == 80

    # L'état est exposé dans /bennes/ tant que le taux ne baisse pas.
    benne = client.get("/bennes/").json()[0]["releve"]["bennes"][0]
    assert benne["rotation_faite"] is True
    assert benne["taux"] == 80  # le taux reste affiché, l'info n'est pas perdue


def test_annuler_rotation_faite(client, site_avec_benne, db):
    client.post(f"/bennes/{site_avec_benne.id}/rotation", json={"type_dechet": "Bois"})
    resp = client.delete(f"/bennes/{site_avec_benne.id}/Bois/rotation-faite")
    assert resp.status_code == 200
    assert resp.json()["rotation_faite"] is False

    t = db.query(models.Tassement).filter_by(site_id=site_avec_benne.id, type_dechet="Bois").first()
    assert t.rotation_faite is False
    assert t.taux_reference is None
