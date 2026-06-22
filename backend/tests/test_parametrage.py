"""Tests du paramétrage des seuils d'alerte par benne."""
from datetime import date

import pytest

from backend import models


@pytest.fixture
def site_id(db):
    site = models.Site(code="LIMAY", nom="Limay", actif=True)
    db.add(site)
    db.flush()
    releve = models.Releve(site_id=site.id, date_releve=date(2026, 6, 20), agent="Test")
    db.add(releve)
    db.flush()
    db.add(models.Benne(releve_id=releve.id, type_dechet="Bois", taux=50, a_compacteur=False))
    db.commit()
    return site.id


def test_update_seuil_valide(client, site_id):
    resp = client.put(f"/parametrage/seuils/{site_id}/Bois", json={"seuil_avertissement": 60, "seuil_critique": 85})
    assert resp.status_code == 200
    body = resp.json()
    assert body["seuil_avertissement"] == 60
    assert body["seuil_critique"] == 85


def test_get_seuils_reflete_la_config(client, site_id):
    client.put(f"/parametrage/seuils/{site_id}/Bois", json={"seuil_avertissement": 60, "seuil_critique": 85})
    resp = client.get("/parametrage/seuils")
    assert resp.status_code == 200
    seuils = {s["type_dechet"]: s for s in resp.json()}
    assert seuils["Bois"]["seuil_avertissement"] == 60
    assert seuils["Bois"]["seuil_critique"] == 85


def test_avertissement_doit_etre_inferieur_au_critique(client, site_id):
    resp = client.put(f"/parametrage/seuils/{site_id}/Bois", json={"seuil_avertissement": 90, "seuil_critique": 80})
    assert resp.status_code == 422


def test_seuil_hors_bornes(client, site_id):
    resp = client.put(f"/parametrage/seuils/{site_id}/Bois", json={"seuil_avertissement": 0, "seuil_critique": 80})
    assert resp.status_code == 422
    resp = client.put(f"/parametrage/seuils/{site_id}/Bois", json={"seuil_avertissement": 50, "seuil_critique": 120})
    assert resp.status_code == 422


def test_update_seuil_site_inconnu(client):
    resp = client.put("/parametrage/seuils/999/Bois", json={"seuil_avertissement": 60, "seuil_critique": 85})
    assert resp.status_code == 404
