# Suivi automatisé des bennes — SOTREMA

Tableau de bord interne pour le suivi en temps réel du taux de remplissage des bennes dans les déchetteries clientes. L'application récupère automatiquement les relevés Kizeo Forms reçus par email (Outlook 365), les persiste en base de données, et expose un dashboard web avec alertes automatiques.

---

## Stack technique

| Couche | Choix | Justification |
|---|---|---|
| Backend | FastAPI (Python 3.11) | Async natif, typage Pydantic, idéal pour les tâches de polling |
| Base de données | PostgreSQL 15 | Historisation des relevés, requêtes temporelles |
| ORM | SQLAlchemy 2.0 + Alembic | Migrations versionnées, typage strict |
| Parsing PDF | pdfplumber | Extraction fiable de PDFs Kizeo à structure fixe |
| Intégration mail | Microsoft Graph API (MSAL) | Outlook 365 sans configuration serveur mail |
| Alertes | SMTP via Outlook 365 | Réutilise l'infra mail existante |
| Frontend | React 18 + Vite | SPA légère, rechargement automatique |
| Planificateur | APScheduler (in-process) | Polling toutes les 5 min, sans dépendance Airflow |
| Conteneurisation | Docker + Docker Compose | Déploiement reproductible sur Linux intranet |

---

## Architecture du projet

```
sotrema-bennes/
├── backend/
│   ├── main.py                  # Point d'entrée FastAPI + APScheduler
│   ├── config.py                # Variables d'environnement (pydantic-settings)
│   ├── database.py              # Engine SQLAlchemy, SessionLocal
│   ├── models.py                # Modèles ORM (Site, Releve, Benne, Alerte)
│   ├── schemas.py               # Schémas Pydantic (requête/réponse)
│   ├── routers/
│   │   ├── bennes.py            # GET /bennes, GET /bennes/{site_id}
│   │   ├── alertes.py           # GET /alertes, GET /alertes/actives
│   │   └── sync.py              # POST /sync/manual, GET /sync/status
│   ├── services/
│   │   ├── graph_watcher.py     # Polling Microsoft Graph API
│   │   ├── pdf_parser.py        # Extraction données Kizeo Forms PDF
│   │   ├── ingestion.py         # Persistance en base + déduplication
│   │   └── alertes.py           # Détection seuils + envoi email
│   └── migrations/              # Alembic
│       └── versions/
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   └── client.js        # Axios avec base URL configurable
│   │   ├── components/
│   │   │   ├── SiteCard.jsx     # Carte site avec bennes déroulables
│   │   │   ├── BenneRow.jsx     # Ligne benne avec barre de remplissage
│   │   │   ├── AlerteBadge.jsx  # Badge statut coloré
│   │   │   └── SyncStatus.jsx   # Dernière synchro + bouton manuel
│   │   └── pages/
│   │       ├── Dashboard.jsx    # Vue principale sites + KPIs
│   │       ├── Alertes.jsx      # Alertes actives + historique envois
│   │       └── Historique.jsx   # Relevés + graphique taux moyens
│   ├── index.html
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Modèle de données

```sql
-- Sites clients (déchetteries)
CREATE TABLE sites (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50) UNIQUE NOT NULL,   -- ex: "TRIEL"
    nom         VARCHAR(200) NOT NULL,
    actif       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Relevés journaliers (un par email reçu)
CREATE TABLE releves (
    id              SERIAL PRIMARY KEY,
    site_id         INTEGER REFERENCES sites(id),
    date_releve     DATE NOT NULL,
    agent           VARCHAR(200),
    email_message_id VARCHAR(500) UNIQUE,      -- ID Graph API, pour déduplication
    recu_at         TIMESTAMP DEFAULT NOW()
);

-- État de chaque benne dans un relevé
CREATE TABLE bennes (
    id          SERIAL PRIMARY KEY,
    releve_id   INTEGER REFERENCES releves(id) ON DELETE CASCADE,
    type_dechet VARCHAR(100) NOT NULL,          -- ex: "Ferraille", "Bois"
    taux        INTEGER NOT NULL CHECK (taux BETWEEN 0 AND 100),
    a_compacteur BOOLEAN DEFAULT FALSE
);

-- Historique des alertes envoyées
CREATE TABLE alertes (
    id              SERIAL PRIMARY KEY,
    benne_id        INTEGER REFERENCES bennes(id),
    seuil_declenche INTEGER NOT NULL,           -- taux au moment de l'alerte
    email_destinataire VARCHAR(200),
    envoye_at       TIMESTAMP DEFAULT NOW(),
    statut          VARCHAR(50) DEFAULT 'envoye'
);

-- Index utiles
CREATE INDEX idx_releves_site_date ON releves(site_id, date_releve DESC);
CREATE INDEX idx_bennes_type ON bennes(type_dechet);
CREATE INDEX idx_alertes_benne ON alertes(benne_id);
```

---

## Variables d'environnement

Créer un fichier `.env` à la racine à partir de `.env.example` :

```env
# PostgreSQL
DATABASE_URL=postgresql://sotrema:motdepasse@localhost:5432/sotrema_bennes

# Microsoft Graph API (Azure App Registration)
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=votre_secret_azure
OUTLOOK_USER_EMAIL=pipeline@sotrema.fr

# Alertes
ALERTE_SEUIL=75                          # Taux déclenchant une alerte (%)
ALERTE_DESTINATAIRE=exploitation@sotrema.fr
SMTP_FROM=pipeline@sotrema.fr

# Polling
POLLING_INTERVAL_MINUTES=5

# App
ENVIRONMENT=production
SECRET_KEY=changez_cette_valeur_en_prod
CORS_ORIGINS=http://localhost:5173,http://intranet.sotrema.fr
```

---

## Implémentation — backend

### `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str
    outlook_user_email: str
    alerte_seuil: int = 75
    alerte_destinataire: str
    smtp_from: str
    polling_interval_minutes: int = 5
    environment: str = "production"
    secret_key: str
    cors_origins: list[str] = []

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### `services/graph_watcher.py`

Logique de polling Outlook via Microsoft Graph API.

```python
import msal
import httpx
import logging
from datetime import datetime, timedelta
from backend.config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/.default"]


def get_access_token() -> str:
    app = msal.ConfidentialClientApplication(
        client_id=settings.azure_client_id,
        client_credential=settings.azure_client_secret,
        authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}",
    )
    result = app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" not in result:
        raise RuntimeError(f"Échec authentification Graph API : {result.get('error_description')}")
    return result["access_token"]


async def fetch_kizeo_emails(since: datetime | None = None) -> list[dict]:
    """
    Récupère les emails non lus contenant un PDF Kizeo Forms.
    Filtre sur l'objet et la présence d'une pièce jointe PDF.
    """
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Filtre : emails avec pièce jointe, depuis `since` si fourni
    filter_parts = ["hasAttachments eq true"]
    if since:
        filter_parts.append(f"receivedDateTime ge {since.isoformat()}Z")

    params = {
        "$filter": " and ".join(filter_parts),
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,receivedDateTime,from,hasAttachments",
        "$top": "50",
    }

    url = f"{GRAPH_BASE}/users/{settings.outlook_user_email}/messages"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        messages = resp.json().get("value", [])

    # Filtrer sur "Kizeo" dans l'objet pour éviter les faux positifs
    kizeo_msgs = [m for m in messages if "kizeo" in m.get("subject", "").lower()
                  or "etat des lieux" in m.get("subject", "").lower()]

    logger.info(f"{len(kizeo_msgs)} email(s) Kizeo détecté(s)")
    return kizeo_msgs


async def download_pdf_attachment(message_id: str) -> bytes | None:
    """Télécharge la première pièce jointe PDF d'un message."""
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/users/{settings.outlook_user_email}/messages/{message_id}/attachments"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        attachments = resp.json().get("value", [])

    for att in attachments:
        if att.get("contentType") == "application/pdf":
            import base64
            return base64.b64decode(att["contentBytes"])

    return None
```

---

### `services/pdf_parser.py`

Extraction des données structurées depuis un PDF Kizeo Forms.

```python
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
            # Extraire tout le texte des 5 pages
            full_text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    except Exception as e:
        logger.error(f"Erreur lecture PDF : {e}")
        return None

    lines = [l.strip() for l in full_text.splitlines() if l.strip()]

    # --- Extraction des métadonnées ---
    site = _extract_field(lines, "Déchetterie")
    agent = _extract_field(lines, "Nom")
    date_str = _extract_field(lines, "Date de réponse")
    date_releve = _parse_date(date_str)

    if not site or not date_releve:
        logger.warning("PDF invalide : site ou date manquant")
        return None

    # --- Extraction des bennes ---
    bennes = []
    i = 0
    while i < len(lines):
        matched_type = next(
            (t for t in TYPES_BENNES if lines[i].lower().startswith(t.lower())), None
        )
        if matched_type:
            # La ligne suivante contient le taux (ex: "% : 75%")
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
    return ReleveData(site=site, agent=agent, date_releve=date_releve, bennes=bennes)


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
```

---

### `services/ingestion.py`

Orchestration du pipeline : email → PDF → base de données.

```python
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.services.graph_watcher import fetch_kizeo_emails, download_pdf_attachment
from backend.services.pdf_parser import parse_kizeo_pdf
from backend.services import alertes as alerte_service
from backend import models

logger = logging.getLogger(__name__)


async def run_sync_pipeline(db: Session) -> dict:
    """
    Pipeline complet :
    1. Polling Graph API pour les nouveaux emails Kizeo
    2. Téléchargement et parsing des PDFs joints
    3. Déduplication par message_id
    4. Persistance en base
    5. Déclenchement des alertes si seuil dépassé
    """
    since = datetime.utcnow() - timedelta(hours=24)
    emails = await fetch_kizeo_emails(since=since)

    stats = {"traites": 0, "ignores": 0, "erreurs": 0, "alertes": 0}

    for email in emails:
        message_id = email["id"]

        # Déduplication : ignorer si déjà traité
        existing = db.query(models.Releve).filter_by(email_message_id=message_id).first()
        if existing:
            stats["ignores"] += 1
            continue

        pdf_bytes = await download_pdf_attachment(message_id)
        if not pdf_bytes:
            logger.warning(f"Pas de PDF pour le message {message_id}")
            stats["erreurs"] += 1
            continue

        releve_data = parse_kizeo_pdf(pdf_bytes)
        if not releve_data:
            stats["erreurs"] += 1
            continue

        # Upsert site
        site = db.query(models.Site).filter_by(code=releve_data.site.upper()).first()
        if not site:
            site = models.Site(code=releve_data.site.upper(), nom=releve_data.site)
            db.add(site)
            db.flush()

        # Créer le relevé
        releve = models.Releve(
            site_id=site.id,
            date_releve=releve_data.date_releve,
            agent=releve_data.agent,
            email_message_id=message_id,
        )
        db.add(releve)
        db.flush()

        # Créer les bennes et déclencher les alertes
        for b in releve_data.bennes:
            benne = models.Benne(
                releve_id=releve.id,
                type_dechet=b.type_dechet,
                taux=b.taux,
                a_compacteur=b.a_compacteur,
            )
            db.add(benne)
            db.flush()

            if b.taux >= 75:
                await alerte_service.envoyer_alerte(db=db, benne=benne, site=site)
                stats["alertes"] += 1

        db.commit()
        stats["traites"] += 1
        logger.info(f"Relevé persisté : {site.nom} · {releve_data.date_releve}")

    return stats
```

---

### `services/alertes.py`

```python
import smtplib
import logging
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
from backend.config import settings
from backend import models

logger = logging.getLogger(__name__)


async def envoyer_alerte(db: Session, benne: models.Benne, site: models.Site) -> None:
    """Envoie un email d'alerte et persiste l'entrée en base."""

    # Eviter les doublons sur un même relevé
    existing = db.query(models.Alerte).filter_by(benne_id=benne.id).first()
    if existing:
        return

    sujet = f"[SOTREMA] Rotation urgente — {benne.type_dechet} · {site.nom} ({benne.taux}%)"
    corps = (
        f"Bonjour,\n\n"
        f"La benne {benne.type_dechet} sur le site {site.nom} "
        f"atteint {benne.taux}% de remplissage.\n"
        f"Une rotation est à planifier en priorité.\n\n"
        f"— Système automatique SOTREMA"
    )

    try:
        msg = MIMEText(corps)
        msg["Subject"] = sujet
        msg["From"] = settings.smtp_from
        msg["To"] = settings.alerte_destinataire

        with smtplib.SMTP("smtp.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_from, settings.azure_client_secret)
            smtp.send_message(msg)

        alerte = models.Alerte(
            benne_id=benne.id,
            seuil_declenche=benne.taux,
            email_destinataire=settings.alerte_destinataire,
            statut="envoye",
        )
        db.add(alerte)
        logger.info(f"Alerte envoyée : {benne.type_dechet} · {site.nom}")

    except Exception as e:
        logger.error(f"Échec envoi alerte : {e}")
```

---

### `routers/bennes.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas

router = APIRouter(prefix="/bennes", tags=["bennes"])


@router.get("/", response_model=list[schemas.SiteAvecDerniereReleve])
def get_tous_les_sites(db: Session = Depends(get_db)):
    """
    Retourne l'état actuel de tous les sites actifs
    avec les taux du dernier relevé.
    """
    sites = db.query(models.Site).filter_by(actif=True).all()
    result = []
    for site in sites:
        dernier_releve = (
            db.query(models.Releve)
            .filter_by(site_id=site.id)
            .order_by(models.Releve.date_releve.desc())
            .first()
        )
        result.append(schemas.SiteAvecDerniereReleve(
            site=site,
            releve=dernier_releve,
        ))
    return result


@router.get("/{site_id}/historique", response_model=list[schemas.ReleveDetail])
def get_historique_site(site_id: int, jours: int = 30, db: Session = Depends(get_db)):
    """Historique des relevés d'un site sur N jours."""
    from datetime import date, timedelta
    depuis = date.today() - timedelta(days=jours)
    return (
        db.query(models.Releve)
        .filter(models.Releve.site_id == site_id, models.Releve.date_releve >= depuis)
        .order_by(models.Releve.date_releve.desc())
        .all()
    )
```

---

### `main.py`

```python
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.routers import bennes, alertes, sync
from backend.services.ingestion import run_sync_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    async def polling_job():
        db = SessionLocal()
        try:
            stats = await run_sync_pipeline(db)
            logger.info(f"Polling terminé : {stats}")
        finally:
            db.close()

    scheduler.add_job(
        polling_job,
        "interval",
        minutes=settings.polling_interval_minutes,
        id="kizeo_polling",
    )
    scheduler.start()
    logger.info(f"Polling démarré (toutes les {settings.polling_interval_minutes} min)")

    yield

    scheduler.shutdown()


app = FastAPI(
    title="SOTREMA — Suivi des bennes",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bennes.router)
app.include_router(alertes.router)
app.include_router(sync.router)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.environment}
```

---

## Docker Compose

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: sotrema_bennes
      POSTGRES_USER: sotrema
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sotrema"]
      interval: 10s
      retries: 5

  backend:
    build: ./backend
    restart: unless-stopped
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## Installation et démarrage

```bash
# 1. Cloner le dépôt
git clone https://github.com/sotrema/suivi-bennes.git
cd suivi-bennes

# 2. Configurer l'environnement
cp .env.example .env
# Éditer .env avec les vraies valeurs Azure + PostgreSQL

# 3. Lancer les services
docker compose up -d --build

# 4. Appliquer les migrations Alembic
docker compose exec backend alembic upgrade head

# 5. Vérifier que l'API répond
curl http://localhost:8000/health
# {"status": "ok", "env": "production"}

# 6. Frontend accessible sur
# http://localhost:3000  (ou http://intranet.sotrema.fr:3000 en réseau local)
```

---

## Configuration Azure App Registration

Étapes à réaliser une seule fois dans le portail Azure de la SOTREMA :

1. **Azure Active Directory** → App registrations → New registration
2. Nom : `sotrema-bennes-pipeline` · Type : *Single tenant*
3. **Certificates & secrets** → New client secret → copier la valeur dans `.env`
4. **API permissions** → Add permission → Microsoft Graph → Application permissions :
   - `Mail.Read` — lecture des emails
   - `Mail.Send` — envoi des alertes
5. **Grant admin consent** (nécessite un compte admin Azure)
6. Copier **Tenant ID** et **Client ID** dans `.env`

---

## Endpoints API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/health` | Statut de l'application |
| `GET` | `/bennes` | État actuel de tous les sites |
| `GET` | `/bennes/{site_id}/historique` | Historique N jours d'un site |
| `GET` | `/alertes/actives` | Alertes non résolues |
| `GET` | `/alertes` | Historique complet des alertes |
| `POST` | `/sync/manual` | Déclencher une synchro manuelle |
| `GET` | `/sync/status` | Dernière synchro + stats |

---

## Dépendances Python

```txt
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
pydantic-settings==2.2.1
pdfplumber==0.11.0
msal==1.28.0
httpx==0.27.0
apscheduler==3.10.4
psycopg2-binary==2.9.9
python-multipart==0.0.9
```

---

## Points d'attention pour Claude Code

- Le parser PDF (`pdf_parser.py`) doit être testé sur **plusieurs PDFs réels** avant mise en production. La structure Kizeo est fixe mais peut varier selon la version du formulaire. Ajouter des tests unitaires avec des PDFs de chaque déchetterie.
- La déduplication repose sur `email_message_id` (ID unique Graph API). Ne pas utiliser la date seule — un même site peut envoyer deux relevés le même jour.
- Les migrations Alembic doivent être générées proprement (`alembic revision --autogenerate`) et revues avant `upgrade head`. Ne pas modifier les modèles directement en base.
- Prévoir un mécanisme de retry sur `fetch_kizeo_emails` en cas d'échec réseau (token expiré, timeout Graph API).
- En production, placer l'application derrière un reverse proxy Nginx avec HTTPS même en intranet.
