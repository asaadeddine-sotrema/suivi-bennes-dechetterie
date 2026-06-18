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
]

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

    site = _extract_field(lines, "Déchetterie")
    agent = _extract_field(lines, "Nom")
    date_str = _extract_field(lines, "Date de réponse")
    date_releve = _parse_date(date_str)

    if not site or not date_releve:
        logger.warning("PDF invalide : site ou date manquant")
        return None

    bennes = []
    i = 0
    while i < len(lines):
        matched_type = next(
            (t for t in TYPES_BENNES if lines[i].lower().startswith(t.lower())), None
        )
        if matched_type:
            taux = None
            for j in range(i + 1, min(i + 4, len(lines))):
                m = PATTERN_PCT.search(lines[j])
                if m:
                    taux = int(m.group(1))
                    break

            if taux is not None and "Compacteur" not in matched_type:
                bennes.append(BenneData(
                    type_dechet=matched_type,
                    taux=taux,
                    a_compacteur=False,
                ))
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
