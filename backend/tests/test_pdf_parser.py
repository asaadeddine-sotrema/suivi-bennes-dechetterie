"""Tests du parseur de PDF Kizeo (fonctions pures)."""
from datetime import date

from backend.services.pdf_parser import _extract_field, _parse_date, parse_kizeo_pdf, est_type_exclu


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


def test_types_exclus():
    # Verre, emballage et mobilier ne sont pas suivis (y compris avec un suffixe numéroté).
    assert est_type_exclu("Borne Verre")
    assert est_type_exclu("Borne Emballage")
    assert est_type_exclu("Mobilier")
    assert est_type_exclu("Mobilier 1")
    # Les autres types restent suivis.
    assert not est_type_exclu("Bois")
    assert not est_type_exclu("Carton")
    assert not est_type_exclu("Gravât")
