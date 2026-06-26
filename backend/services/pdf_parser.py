import pdfplumber
import re
import io
import logging
from dataclasses import dataclass, field
from datetime import date

logger = logging.getLogger(__name__)

TYPES_BENNES = [
    "Plâtre", "Encombrant", "Compacteur Encombrant", "Déchets vert",
    "Bois", "Compacteur Bois", "Gravât", "Ferraille", "Compacteur Ferraille",
    "Carton", "Compacteur Carton", "Borne Verre", "Borne Emballage", "Mobilier",
    "Benne de Plâtre", "Compacteurs Encombrant", "Benne de Déchets verts", "Compacteur de Bois",
    "Benne de Gravats", "Compacteur de Ferrailles", "Compacteur de Cartons", 
]

# Types de bennes volontairement ignorés (non suivis, exclus des alertes et des stats).
TYPES_EXCLUS = ("Borne Verre", "Borne Emballage", "Mobilier")


def est_type_exclu(type_dechet) -> bool:
    """Vrai si le type de déchet ne doit pas être suivi (verre, emballage, mobilier)."""
    return str(type_dechet).startswith(TYPES_EXCLUS)


# Déchèteries qui ne disposent d'aucun compacteur : tout compacteur y est ignoré,
# même si le PDF en mentionne un. (Correspondance insensible à la casse / aux préfixes.)
SITES_SANS_COMPACTEUR = ("closeaux 1",)


def site_sans_compacteur(site) -> bool:
    s = str(site).lower()
    return any(motif in s for motif in SITES_SANS_COMPACTEUR)

PATTERN_PCT = re.compile(r"(\d{1,3})%")
PATTERN_DATE = re.compile(r"(\d{2}/\d{2}/\d{4})")


@dataclass
class BenneData:
    type_dechet: str
    taux: int
    a_compacteur: bool = False


@dataclass
class ReleveData:
    site: str
    agent: str
    date_releve: date
    bennes: list[BenneData] = field(default_factory=list)


def parse_kizeo_pdf(pdf_bytes: bytes) -> ReleveData | None:
    """
    Parse un PDF Kizeo Forms 'Etat des lieux des bennes (Journalier)'.
    Retourne un ReleveData structuré ou None si le format est invalide.
    """
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    except Exception as e:
        logger.error(f"Erreur lecture PDF : {e}")
        return None

    lines = [l.strip() for l in full_text.splitlines() if l.strip()]

    site = _extract_field(lines, "Prénom")
    agent = _extract_field(lines, "Nom")
    date_str = _extract_field(lines, "Date de réponse")
    date_releve = _parse_date(date_str)

    if not site or not date_releve:
        logger.warning("PDF invalide : site ou date manquant")
        return None

    bennes = []
    ignorer_compacteurs = site_sans_compacteur(site)
    i = 0
    while i < len(lines):
        matched_type = next(
            (t for t in TYPES_BENNES if lines[i].lower().startswith(t.lower())), None
        )
        if matched_type and not est_type_exclu(matched_type):
            a_compacteur = matched_type.lower().startswith("compacteur")
            # Le nombre peut être négatif : « -1 » (comme « 0 ») signifie « il n'y en a pas ».
            count_m = re.search(r':\s*(-?\d+)\s*$', lines[i])
            count = int(count_m.group(1)) if count_m else 1

            taux_list = []
            absent = False
            for j in range(i + 1, min(i + 5, len(lines))):
                lj = lines[j].strip()
                # On s'arrête si on atteint déjà le type suivant.
                if any(lj.lower().startswith(t.lower()) for t in TYPES_BENNES):
                    break
                # La ligne de taux de CE type commence par « % ».
                if lj.startswith("%"):
                    # « Pas de compacteur / Pas de benne » : on ignore, même si un nombre est indiqué.
                    if "pas de" in lj.lower():
                        absent = True
                    else:
                        taux_list = [int(p) for p in PATTERN_PCT.findall(lj)]
                    break

            if a_compacteur and ignorer_compacteurs:
                absent = True  # site sans compacteur : on ignore

            if not absent and taux_list and count > 0:
                for k in range(count):
                    t = taux_list[k] if k < len(taux_list) else taux_list[0]
                    label = matched_type if count == 1 else f"{matched_type} {k + 1}"
                    bennes.append(BenneData(type_dechet=label, taux=t, a_compacteur=a_compacteur))
        i += 1

    logger.info(f"PDF parsé : {site} · {date_releve} · {len(bennes)} bennes")
    return ReleveData(site=site, agent=agent or "", date_releve=date_releve, bennes=bennes)


def _extract_field(lines: list[str], label: str) -> str | None:
    for line in lines:
        if line.startswith(f"{label} :") or line.startswith(f"{label}:"):
            parts = line.split(":", 1)
            return parts[1].strip() if len(parts) > 1 else None
    return None


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    m = PATTERN_DATE.search(date_str)
    if m:
        from datetime import datetime
        return datetime.strptime(m.group(1), "%d/%m/%Y").date()
    return None
