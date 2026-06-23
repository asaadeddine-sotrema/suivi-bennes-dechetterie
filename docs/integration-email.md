# Intégration email — récupération automatique des PDF Kizeo

Ce document décrit la mise en place de la **synchronisation automatique** des rapports
PDF envoyés par **Kizeo Forms** par email, via **Microsoft Graph** (mode application,
sans connexion utilisateur interactive).

- L'application lit une **boîte mail partagée dédiée** et importe les nouveaux PDF.
- Accès **en lecture seule** (`Mail.Read`), restreint à cette seule boîte.
- **Aucune licence supplémentaire** : boîte partagée gratuite, App Registration et
  Microsoft Graph gratuits.

---

## 1. Demande à envoyer au responsable IT

> **Objet :** Demande de configuration — boîte mail partagée + accès Microsoft Graph
> (application interne « Suivi des bennes »)
>
> Bonjour [Prénom / équipe IT],
>
> Dans le cadre de l'application interne de **suivi du remplissage des bennes**, j'ai
> besoin d'automatiser la récupération des rapports PDF envoyés par **Kizeo Forms** par
> email. L'application se connecte à Microsoft 365 **en mode application (service, sans
> connexion utilisateur interactive)** et lit une boîte mail dédiée pour importer les
> nouveaux PDF.
>
> Pourriez-vous mettre en place les éléments suivants ?
>
> **1. Une boîte aux lettres partagée dédiée**
> - Créer une **boîte partagée** (*shared mailbox*), ex. `bennes@[domaine].fr`.
> - Une boîte partagée **ne nécessite pas de licence** (jusqu'à 50 Go) — merci de
>   privilégier cette option plutôt qu'une boîte utilisateur licenciée.
> - C'est l'adresse qui recevra les rapports Kizeo.
>
> **2. Une stratégie de rétention sur cette boîte**
> - Appliquer une **règle de rétention** supprimant automatiquement les messages de
>   **plus de 30 jours**.
> - Les originaux étant conservés dans la boîte d'archivage `[boîte d'archive existante]`,
>   cette purge n'entraîne aucune perte.
>
> **3. Une inscription d'application (App Registration) dans Entra ID (Azure AD)**
> - Nom suggéré : `SuiviBennes-Kizeo`.
> - Application confidentielle de type service/daemon, **sans URI de redirection**
>   (flux *client credentials*).
>
> **4. Une permission Microsoft Graph — en lecture seule**
> - **`Mail.Read`** de type **Application** (et non « Déléguée »).
> - ⚠️ Merci d'**accorder le consentement administrateur** pour cette permission.
> - L'application n'a besoin **que de lire** les emails — aucun accès en
>   écriture/suppression n'est requis.
>
> **5. Restreindre l'accès à la seule boîte dédiée (moindre privilège)**
> Par défaut, `Mail.Read` (Application) donne accès à **toutes** les boîtes. Merci de
> limiter l'application à la seule boîte ci-dessus via une **Application Access Policy**
> Exchange Online :
> ```powershell
> New-ApplicationAccessPolicy -AppId <CLIENT_ID> `
>   -PolicyScopeGroupId bennes@[domaine].fr `
>   -AccessRight RestrictAccess `
>   -Description "Limite l'app SuiviBennes-Kizeo a la boite bennes"
> ```
>
> **6. Un secret client**
> - Générer un **client secret** et m'en transmettre **la valeur** (visible une seule fois).
> - M'indiquer **sa date d'expiration** : il devra être renouvelé avant échéance, sinon la
>   synchronisation s'arrêtera.
>
> ---
>
> **Informations à me retourner :**
>
> | Information | Où la trouver |
> |---|---|
> | **Tenant ID** (ID de l'annuaire) | Vue d'ensemble de l'App Registration |
> | **Client ID** (ID d'application) | Vue d'ensemble de l'App Registration |
> | **Client Secret** (la *valeur*) | Onglet « Certificats & secrets » |
> | **Adresse de la boîte partagée** | (celle créée au point 1) |
>
> Le client secret étant sensible, merci de me le transmettre par un **canal sécurisé**
> (gestionnaire de secrets, message protégé, en main propre).
>
> **Récapitulatif des coûts** : aucune licence supplémentaire (boîte partagée gratuite,
> App Registration et Microsoft Graph gratuits).
>
> Merci d'avance pour votre aide. Je reste disponible pour tout complément technique.
>
> Cordialement,
> [Ton nom] — [Fonction / service]

---

## 2. Configuration de l'application (une fois les informations reçues)

Renseigner les valeurs dans le fichier `.env` à la racine du projet :

```dotenv
AZURE_TENANT_ID=...        # Tenant ID
AZURE_CLIENT_ID=...        # Client ID
AZURE_CLIENT_SECRET=...    # valeur du secret client
OUTLOOK_USER_EMAIL=...     # adresse de la boîte partagée (ex. bennes@domaine.fr)

SYNC_ENABLED=true          # active la synchronisation automatique
SYNC_INTERVAL_MINUTES=5    # fréquence de relève (voir § Fréquence)
```

Puis redémarrer :

```bash
make restart
```

Au démarrage, le journal doit indiquer :
`Planificateur de synchronisation actif (toutes les 5 min)`.

On peut aussi déclencher une relève **manuelle** depuis le tableau de bord
(bouton « Synchroniser maintenant », réservé aux administrateurs).

---

## 3. Fréquence de relève (`SYNC_INTERVAL_MINUTES`)

- Minimum technique : **1 minute** (valeur entière en minutes).
- Microsoft Graph n'est **pas** un facteur limitant à ce rythme (loin des quotas).
- La relève **déduplique par `message_id`** : interroger souvent ne crée pas de doublons.
- **Recommandé : 5 minutes** — quasi temps réel ressenti, charge négligeable.
- Pour du vrai temps réel, la bonne approche serait les **webhooks Microsoft Graph**
  (notifications push), mais c'est surdimensionné pour ce besoin.

---

## 4. Points de vigilance

- **Expiration du secret client** : noter la date dans un rappel. C'est la cause n°1 de
  panne de ce type d'intégration — la synchro s'arrête silencieusement à l'expiration.
- **Côté Kizeo** : le formulaire doit envoyer le PDF **en pièce jointe** à la boîte dédiée.
  L'application ne retient que les emails dont l'objet contient « kizeo » ou
  « etat des lieux ».
- **Fenêtre de relève** : seules les **dernières 24 h** d'emails sont examinées à chaque
  cycle. Si l'application reste arrêtée plus de 24 h, des rapports plus anciens pourraient
  être manqués (la fenêtre peut être élargie si besoin).
- **Archivage avant purge** : confirmer que la boîte d'archivage reçoit bien une **copie
  indépendante** des mails avant d'activer la rétention 30 jours sur la boîte de travail.

---

## 5. Sécurité — choix retenus

- Accès Graph **en lecture seule** (`Mail.Read`), **restreint** à la boîte dédiée
  (Application Access Policy) → moindre privilège.
- Le secret client est stocké dans `.env` (non versionné — voir `.gitignore`).
- Le cycle de vie des messages est géré par **Exchange** (rétention), pas par
  l'application, qui n'a donc aucun droit de suppression.
