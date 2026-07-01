# Demande IT — consentement pour l'automatisation des mails

Mail prêt à envoyer au service informatique. À compléter avant envoi :
`[Prénom]` (IT), `prenom.nom@sotrema.fr` (identifiant admin, ligne PowerShell), `[Ton nom]`.

---

**Objet :** Demande de consentement administrateur – application « suivi-bennes-dechetterie »

Bonjour [Prénom],

Dans le cadre du suivi des bennes en déchèterie, j'ai développé un petit outil interne qui récupère automatiquement les relevés Kizeo reçus par mail. Pour qu'il puisse lire la boîte partagée dédiée, j'ai créé une application dans Entra ID, mais il me manque ton intervention pour la finaliser : le consentement ne peut être validé que par un compte administrateur.

Il y aurait deux choses à faire de ton côté.

D'abord, sur l'app registration :
- Application : suivi-bennes-dechetterie
- App (client) ID : 3b07dc32-806b-485d-819c-97f98ee26a4d
- Tenant ID : 0ace70f4-2011-4e13-a838-b5913bcc710d

Il faut ajouter la permission Microsoft Graph → Application → Mail.Read (si elle n'y est pas déjà), puis cliquer sur « Grant admin consent ».

Ensuite, pour la sécurité, je voudrais que l'application soit restreinte à la seule boîte `bennes-dechetteries@sotrema.fr`. Sans ça, la permission Mail.Read donne un accès en lecture à toutes les boîtes du tenant, ce que je préfère éviter. Ça se règle avec une Application Access Policy sur Exchange Online :

```powershell
Connect-ExchangeOnline -UserPrincipalName prenom.nom@sotrema.fr

New-DistributionGroup -Name "Graph-SuiviBennes" -Type Security -Members bennes-dechetteries@sotrema.fr

New-ApplicationAccessPolicy -AppId 3b07dc32-806b-485d-819c-97f98ee26a4d -PolicyScopeGroupId Graph-SuiviBennes -AccessRight RestrictAccess -Description "Suivi bennes : acces limite a la boite Kizeo"

Test-ApplicationAccessPolicy -AppId 3b07dc32-806b-485d-819c-97f98ee26a4d -Identity bennes-dechetteries@sotrema.fr
```

L'outil tourne uniquement sur le réseau interne et je gère le secret de mon côté, il n'a donc pas à transiter.

Je reste dispo si tu as des questions ou si tu préfères qu'on en parle directement.

Merci d'avance,
[Ton nom]
