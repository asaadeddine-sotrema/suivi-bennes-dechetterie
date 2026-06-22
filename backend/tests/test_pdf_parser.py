"""Tests du parseur de PDF Kizeo (fonctions pures)."""
from datetime import date

from backend.services.pdf_parser import _extract_field, _parse_date, parse_kizeo_pdf


def test_extract_field_avec_espace():
    lines = ["Déchetterie : Limay", "Nom : Dupont"]
    assert _extract_field(lines, "Déchetterie") == "Limay"
    assert _extract_field(lines, "Nom") == "Dupont"


def test_extract_field_sans_espace():
    lines = ["Déchetterie:Triel"]
    assert _extract_field(lines, "Déchetterie") == "Triel"


def test_extract_field_absent():
    assert _extract_field(["Autre : valeur"], "Déchetterie") is None


def test_parse_date_valide():
    assert _parse_date("Date de réponse : 12/02/2026 14:30") == date(2026, 2, 12)


def test_parse_date_none_et_invalide():
    assert _parse_date(None) is None
    assert _parse_date("pas de date ici") is None


def test_parse_pdf_invalide_renvoie_none():
    # Des octets qui ne sont pas un PDF : le parseur doit renvoyer None, pas planter.
    assert parse_kizeo_pdf(b"ceci n'est pas un pdf") is None
