# Spécifications d'Implémentation : Tassement Planifié (Coupe-circuit d'alerte)

**Rôle attendu de l'IA :** Ingénieur Fullstack Senior (FastAPI / React)
**Objectif :** Implémenter une planification de tassement "zéro friction" pour bloquer les alertes automatiques sans alourdir l'UX.

---

## Instructions strictes à suivre

Nous allons implémenter une fonctionnalité de "Tassement planifié" pour couper le circuit des alertes automatiques sans surcharger l'interface utilisateur. Je refuse l'ajout de lourds composants de calendrier par défaut. L'objectif est la "zéro friction" pour les opérateurs sur le terrain.

Voici le plan d'implémentation strict, étape par étape :

### 1. Base de données & Modèles (`backend/models.py`, `backend/schemas.py`)
- Modifie le modèle SQLAlchemy `Tassement` existant. Ajoute une colonne `tassement_prevu_at = Column(TIMESTAMP, nullable=True)`.
- Génère la commande Alembic pour créer la migration correspondante (`alembic revision --autogenerate -m "add_tassement_prevu"`).
- Mets à jour les schémas Pydantic associés (`schemas.py`) pour inclure ce nouveau champ dans les requêtes et réponses.

### 2. API & Logique métier (`backend/routers/bennes.py`)
- Crée une nouvelle route `POST /bennes/{site_id}/{type_dechet}/planifier-tassement`.
- Cette route doit accepter un payload avec une date/heure de planification et mettre à jour (ou créer) l'entrée dans la table `Tassement`.

### 3. Le Coupe-Circuit d'Alertes (`backend/services/ingestion.py`)
- Modifie la logique d'ingestion. Lorsqu'un PDF est parsé et qu'une benne dépasse le seuil critique (ex: 75%), avant d'appeler `alerte_service.envoyer_alerte`, vérifie la table `Tassement` pour ce `site_id` et `type_dechet`.
- **Règle stricte :** Si `tassement_prevu_at` est défini ET qu'il est dans le futur par rapport à `datetime.now()`, **ne déclenche pas l'alerte**. Logue simplement l'information : "Alerte ignorée : tassement planifié le X".

### 4. Frontend : UX "Zéro Friction" (`frontend/src/components/BenneRow.jsx`)
- Sur la ligne d'une benne, ajoute une petite icône/bouton d'action "Planifier".
- Au clic, n'ouvre SURTOUT PAS un `DatePicker` complexe immédiatement. Ouvre un petit menu (popover/dropdown) avec 4 actions rapides qui calculent la date côté client et appellent l'API directement :
  1. ⚡ "Ce matin (12h00)" (Date du jour à 12:00)
  2. 🚗 "Cet après-midi (18h00)" (Date du jour à 18:00)
  3. 📅 "Demain (12h00)" (J+1 à 12:00)
  4. ⚙️ "Date personnalisée..." (Seulement ici, tu peux utiliser un champ de type `datetime-local` standard du navigateur).

### 5. Frontend : Retour Visuel (`frontend/src/components/AlerteBadge.jsx` ou équivalent)
- Si la benne a un `tassement_prevu_at` dans le futur, modifie son affichage visuel. Elle ne doit plus être en rouge critique. 
- Affiche un badge ou une icône (ex: horloge) indiquant clairement "Tassement prévu le [Date/Heure formattée]".

> **Note :** Génère le code fichier par fichier, en t'assurant que les imports sont corrects et que la syntaxe respecte l'architecture existante.
