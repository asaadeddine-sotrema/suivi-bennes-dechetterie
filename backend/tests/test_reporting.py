"""Tests des endpoints de reporting (export CSV + statistiques)."""
from datetime import date

import pytest

from backend import models


@pytest.fixture
def site_avec_donnees(db):
    site = models.Site(code="LIMAY", nom="Limay", actif=True)
    db.add(site)
    db.flush()
    releve = models.Releve(site_id=site.id, date_releve=date(2026, 6, 20), agent="Dupont")
    db.add(releve)
    db.flush()
    db.add(models.Benne(releve_id=releve.id, type_dechet="Bois", taux=80, a_compacteur=False))
    db.add(models.Benne(releve_id=releve.id, type_dechet="Borne Verre", taux=50, a_compacteur=False))  # exclue
    db.add(models.HistoriqueTassement(site_id=site.id, type_dechet="Bois", evenement="tassement"))
    db.add(models.HistoriqueTassement(site_id=site.id, type_dechet="Bois", evenement="rotation"))
    db.commit()
    return site


def test_export_csv(client, site_avec_donnees):
    resp = client.get("/reporting/releves.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    lignes = resp.text.strip().splitlines()
    assert lignes[0].startswith("Date;Site;Code")
    assert any("Bois" in l for l in lignes)
    # Les types exclus ne doivent pas apparaître.
    assert not any("Borne Verre" in l for l in lignes)


def test_stats(client, site_avec_donnees):
    resp = client.get("/reporting/stats")
    assert resp.status_code == 200
    data = resp.json()
    site = data["sites"][0]
    assert site["site_nom"] == "Limay"
    assert site["nb_bennes"] == 1          # Borne Verre exclue
    assert site["taux_moyen"] == 80
    assert site["nb_tassements"] == 1
    assert site["nb_rotations"] == 1
    assert data["totaux"]["tassements"] == 1
    assert data["totaux"]["rotations"] == 1
    assert len(data["activite_mensuelle"]) >= 1
