# 📰 Sina Journal

**Ton propre journal du matin, fabriqué automatiquement chaque jour et livré sur ton téléphone.**
Pas de papier, pas d'encre, pas d'appli à ouvrir : à 8h, le numéro du jour t'attend dans ta liseuse (Apple Livres sur iPhone, ReadEra ou une autre appli de lecture sur Android).

- 🗞️ Actualité : Monde, Algérie, Économie, Tech & IA, Sciences, Culture, Sport
- 🕌 Horaires de prière, date hégirienne, verset du jour, météo
- 🖼️ Un tableau de maître chaque jour, en couleur
- ♟️ Un puzzle d'échecs, un quiz, des citations, « Ce jour-là »
- 🇬🇧 🇪🇸 Leçons d'anglais et d'espagnol, arabe & darija
- 🎨 Mise en page de vrai journal : couverture, lettrines, encadrés, mode clair / sépia / nuit

Tout tourne **gratuitement sur GitHub**. Tu choisis ensuite entre deux versions :

| | **Version gratuite** | **Version avec Claude** (IA) |
|---|---|---|
| Prix | **0 €** | Environ 0,20 $ par journal, soit ~7 $/mois (ou ~3-4 $ avec Haiku) |
| Actualité | Revue de presse : titres, extraits et lien vers l'article complet | Articles rédigés et résumés par Claude, plus un dossier du jour |
| La une | Manchette et « L'essentiel » tirés des titres du jour | Manchette rédigée, chiffre, mot, question et intention du jour |
| Leçons de langues, quiz, citations, arabe & darija | ❌ | ✅ |
| Tableau du jour | ✅ (notice du musée, en anglais) | ✅ (présentation en français) |
| Prières, météo, verset, échecs, « Ce jour-là » | ✅ | ✅ |

> 💡 Commence par la version gratuite pour tout installer. Tu pourras ajouter Claude plus tard en 5 minutes.

---

## Sommaire

1. [Comment ça marche](#1-comment-ça-marche)
2. [Ce qu'il te faut](#2-ce-quil-te-faut)
3. [Installation sur GitHub (pas à pas)](#3-installation-sur-github-pas-à-pas)
4. [Ajouter Claude (facultatif)](#4-ajouter-claude-facultatif)
5. [Le jeton GitHub (pour lancer le journal depuis ton téléphone)](#5-le-jeton-github)
6. [Recevoir le journal sur iPhone](#6-recevoir-le-journal-sur-iphone)
7. [Recevoir le journal sur Android](#7-recevoir-le-journal-sur-android)
8. [Autre solution : cron-job.org (iPhone et Android)](#8-autre-solution--cron-joborg)
9. [Personnaliser](#9-personnaliser)
10. [Coûts](#10-coûts)
11. [Sécurité](#11-sécurité)
12. [Dépannage](#12-dépannage)

---

## 1. Comment ça marche

```
 07h00  Ton téléphone (ou cron-job.org) dit à GitHub : « fabrique le journal ! »
          │
          ▼
 GitHub (gratuit) lance journal.py :
   ├─ lit les flux RSS des journaux, la météo, les prières, le verset, les échecs…
   ├─ (version Claude) fait rédiger les articles, leçons, quiz…
   ├─ assemble un ebook mis en page : journal.epub
   └─ le publie à une adresse fixe : https://TON-PSEUDO.github.io/NOM-DU-DEPOT/journal.epub
          │
          ▼
 08h00  Ton téléphone télécharge journal.epub et l'ajoute à ta liseuse 📖
```

**Pourquoi le téléphone lance-t-il le journal ?** GitHub sait lancer des tâches tout seul à heure fixe, mais en pratique il les retarde souvent de plusieurs heures, ou les oublie. Le projet garde ces lancements automatiques **en secours** (entre 4h17 et 6h47), mais c'est ton téléphone à 7h00 qui rend le journal **fiable**. Si le journal du jour existe déjà, les lancements suivants s'arrêtent tout seuls : il n'est jamais fabriqué deux fois.

---

## 2. Ce qu'il te faut

| Quoi | Pour quoi faire | Prix |
|---|---|---|
| Un compte **GitHub** ([github.com](https://github.com)) | Héberger le projet et fabriquer le journal | Gratuit |
| Un **iPhone** (Raccourcis + Livres) **ou** un **Android** (une appli d'automatisation + une liseuse) | Lancer et recevoir le journal | Gratuit |
| *(facultatif)* Un compte **Anthropic** ([console.anthropic.com](https://console.anthropic.com)) | Version avec Claude | Payant à l'usage |

Pas besoin d'ordinateur ni de savoir programmer : **tout peut se faire depuis Safari ou Chrome sur ton téléphone**.

> 📱 **Sur téléphone, utilise le navigateur, pas l'application GitHub** : l'app n'affiche pas les réglages. Si une page s'affiche mal, demande la « version pour ordinateur » (Safari : **aA → Demander le site pour ordinateur** ; Chrome : **⋮ → Version pour ordinateur**).

---

## 3. Installation sur GitHub (pas à pas)

### Étape 1 — Copier le projet dans ton compte

**Le plus simple :** sur la page de ce projet, appuie sur **Fork** (en haut à droite) → **Create fork**. Tu as maintenant ta propre copie, à ton nom.

<details>
<summary>Autre méthode : envoyer les fichiers à la main (depuis un ordinateur)</summary>

1. Sur github.com : **+** → **New repository** → nom, par ex. `sina-journal`, **Public** → **Create repository**.
2. **Add file → Upload files**, puis glisse **tous** les fichiers du projet, y compris le dossier caché `.github` (Mac : `Cmd + Shift + .` pour voir les fichiers cachés ; Windows : **Affichage → Éléments masqués**).
3. **Commit changes**, puis vérifie que `.github/workflows/journal.yml` apparaît bien dans le dépôt.
</details>

> Le dépôt doit être **public** pour que GitHub Pages soit gratuit. Rien de secret n'y est stocké (voir [Sécurité](#11-sécurité)).

### Étape 2 — Activer les Actions

Dans ton dépôt : onglet **Actions**. Si GitHub affiche un bandeau du type *« Workflows aren't being run on this forked repository »*, appuie sur **I understand my workflows, go ahead and enable them**.

### Étape 3 — Activer GitHub Pages

**Settings → Pages → Build and deployment → Source : GitHub Actions.**
N'appuie sur aucun bouton « Configure » : le projet contient déjà tout.

### Étape 4 — Fabriquer ton premier journal

1. Onglet **Actions** → **Journal du matin** (sur téléphone : menu **All workflows ▾**).
2. **Run workflow** → bouton vert **Run workflow**.
3. Attends 1 à 2 minutes, puis recharge la page : une **coche verte ✅** apparaît.
4. Ouvre ton journal :
   ```
   https://TON-PSEUDO.github.io/NOM-DU-DEPOT/journal.epub
   ```
   - `TON-PSEUDO` = ton nom GitHub **en minuscules** ;
   - `NOM-DU-DEPOT` = le nom de ton dépôt (ex. `sinajournal`).

🎉 C'est ta **version gratuite**. Garde bien cette adresse : on en a besoin pour le téléphone.

---

## 4. Ajouter Claude (facultatif)

Claude rédige les articles, la une, le dossier du jour, les leçons, le quiz… C'est payant, mais modeste : environ **0,20 $ par journal** avec le modèle par défaut.

1. Va sur [console.anthropic.com](https://console.anthropic.com) et crée un compte.
2. **Billing** : ajoute un peu de crédit (5 $ suffisent pour commencer). Conseil : fixe une **limite de dépense mensuelle**.
3. **API Keys → Create Key** :
   - **Nom** : `sina-journal` ;
   - **Portée / Workspace** : choisis un **espace de travail** (par ex. « Default »). ⚠️ Une clé sans espace de travail est refusée ;
   - **Expiration** : **Jamais** (sinon le journal perd ses textes le jour où elle expire) ;
   - copie la clé (`sk-ant-…`) : elle ne s'affiche qu'une fois.
4. Dans ton dépôt GitHub : **Settings → Secrets and variables → Actions → New repository secret** :
   - **Name** : `ANTHROPIC_API_KEY` (exactement comme ça) ;
   - **Secret** : colle la clé → **Add secret**.
5. Relance le journal (étape 4 ci-dessus) : cette fois, il est rédigé par Claude.

> 🔒 Ne colle **jamais** ta clé ailleurs que dans ce secret : ni dans un fichier, ni dans un message, ni dans une conversation avec une IA.

**Revenir à la version gratuite :** supprime le secret, ou mets `UTILISER_CLAUDE = False` en haut de `journal.py`.

---

## 5. Le jeton GitHub

Pour que ton téléphone puisse dire à GitHub « fabrique le journal », il lui faut un **jeton** : une sorte de mot de passe limité, qui ne peut **que** lancer ton journal.

1. Ouvre [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new).
2. **Token name** : `Sina Journal téléphone`.
3. **Expiration** : choisis une durée (ou « No expiration »). Note la date si elle expire.
4. **Repository access** → **Only select repositories** → choisis ton dépôt du journal.
5. **Permissions → Repository permissions → Actions** : **Read and write**. (« Metadata : Read-only » s'ajoute tout seul, c'est normal.)
6. **Generate token**, puis copie le jeton (`github_pat_…`). Il ne s'affiche qu'une fois.

> 🔒 Ce jeton ne donne accès ni à ton code ni à ta clé Claude. Garde-le quand même pour toi : ne le publie pas et ne l'envoie à personne.

Tu auras besoin de cette **adresse de lancement** (remplace `TON-PSEUDO` et `NOM-DU-DEPOT`) :
```
https://api.github.com/repos/TON-PSEUDO/NOM-DU-DEPOT/actions/workflows/journal.yml/dispatches
```

---

## 6. Recevoir le journal sur iPhone

Deux automatisations dans l'app **Raccourcis** : une à **7h00** pour lancer le journal, une à **8h00** pour le recevoir.

### Automatisation 1 — 7h00 : lancer le journal

**Raccourcis → Automatisation → + → Heure de la journée**
- **07:00**, **Tous les jours**, **Exécuter immédiatement**, notifications désactivées.

Ajoute **une seule action**, **Obtenir le contenu de l'URL** :

| Réglage | Valeur |
|---|---|
| URL | `https://api.github.com/repos/TON-PSEUDO/NOM-DU-DEPOT/actions/workflows/journal.yml/dispatches` |
| Méthode | `POST` |
| En-tête 1 | `Authorization` → `Bearer github_pat_…` (le mot **Bearer**, une espace, puis ton jeton) |
| En-tête 2 | `Accept` → `application/vnd.github+json` |
| Corps de la requête | `JSON`, un champ **Texte** : `ref` → `main` |

(Les réglages Méthode / En-têtes / Corps apparaissent en touchant la flèche de l'action.)

**Tester :** appuie sur ▶︎. Une réponse vide (« Zéro ko ») est **bon signe**. Dans l'onglet **Actions** de GitHub, un nouveau « Journal du matin » doit apparaître dans les secondes qui suivent.

> ⚠️ Chaque appui sur ▶︎ fabrique un nouveau journal. Avec Claude, chaque fabrication coûte environ 0,20 $ : teste une fois, pas plus.

### Automatisation 2 — 8h00 : recevoir le journal dans Livres

**Raccourcis → Automatisation → + → Heure de la journée**
- **08:00**, **Tous les jours**, **Exécuter immédiatement**, notifications désactivées.

Ajoute ces actions **dans l'ordre** :

| # | Action | Réglage |
|---|---|---|
| 1 | **Obtenir le contenu de l'URL** | `https://TON-PSEUDO.github.io/NOM-DU-DEPOT/journal.epub` |
| 2 | **Définir le nom** | `Sina Journal.epub` |
| 3 | **Ajouter à Livres** | Élément renommé |

> Utilise bien **« Ajouter à Livres »** et non « Ouvrir dans Livres », qui peut échouer quand l'iPhone est verrouillé. Et vérifie que le nom se termine par **`.epub`**.

**Tester :** appuie sur ▶︎. Le journal arrive dans **Livres → Bibliothèque**, avec sa couverture. Ce raccourci ne fait que télécharger : il est gratuit, tu peux l'utiliser autant que tu veux.

### Méthode express iOS 27 : création par message

Colle ces textes dans la création d'automatisation (remplace les valeurs en MAJUSCULES), puis vérifie chaque réglage :

**7h00 :**
```
Crée une automatisation personnelle qui se lance tous les jours à 7h00, exécutée immédiatement, sans confirmation ni notification.
Elle contient une seule action « Obtenir le contenu de l'URL » :
- URL : https://api.github.com/repos/TON-PSEUDO/NOM-DU-DEPOT/actions/workflows/journal.yml/dispatches
- Méthode : POST
- En-têtes : Authorization = Bearer TON_JETON ; Accept = application/vnd.github+json
- Corps de la requête : JSON, avec un champ texte ref = main
```

**8h00 :**
```
Crée une automatisation personnelle qui se lance tous les jours à 8h00, exécutée immédiatement, sans confirmation ni notification.
Elle doit :
1. Télécharger le fichier https://TON-PSEUDO.github.io/NOM-DU-DEPOT/journal.epub
2. Renommer le fichier en « Sina Journal.epub »
3. L'ajouter à l'app Livres avec l'action « Ajouter à Livres ».
```

> 📚 Astuce : crée une collection « Sina Journal » dans Livres, et supprime les anciens numéros de temps en temps (un nouveau livre arrive chaque jour).

---

## 7. Recevoir le journal sur Android

Android n'a pas d'app Raccourcis intégrée : on utilise **[Automate](https://play.google.com/store/apps/details?id=com.llamalab.automate)** (LlamaLab, gratuit) pour les deux tâches, et une liseuse EPUB comme **[ReadEra](https://play.google.com/store/apps/details?id=org.readera)** (gratuite, sans pub) pour lire.

> Les noms des blocs peuvent varier légèrement selon la version d'Automate. On peut aussi faire la même chose avec **Tasker** (payant) ou **MacroDroid**.
> Pour **lancer** le journal, tu peux aussi éviter Automate et utiliser [cron-job.org](#8-autre-solution--cron-joborg) : c'est souvent plus simple.

### Flux 1 — 7h00 : lancer le journal

Dans Automate : **+** (nouveau flux), puis relie ces blocs :

1. **Flow beginning** (déjà présent).
2. **Time await** → *Time* : `07:00`.
3. **HTTP request** :
   - **Request URL** : `https://api.github.com/repos/TON-PSEUDO/NOM-DU-DEPOT/actions/workflows/journal.yml/dispatches`
   - **Request method** : `POST`
   - **Request content type** : `application/json`
   - **Request content** : `{"ref":"main"}`
   - **Request headers** : `{"Authorization": "Bearer TON_JETON", "Accept": "application/vnd.github+json"}`
4. Relie la sortie de **HTTP request** au bloc **Time await**, pour que le flux recommence le lendemain.

Enregistre, puis **Start**.

### Flux 2 — 8h00 : télécharger le journal

Nouveau flux :

1. **Flow beginning**.
2. **Time await** → `08:00`.
3. **HTTP request** :
   - **Request URL** : `https://TON-PSEUDO.github.io/NOM-DU-DEPOT/journal.epub`
   - **Request method** : `GET`
   - **Save response** : *Save to file* → `Download/SinaJournal/Sina Journal.epub`
4. *(facultatif)* **Notification show** : « Ton journal est arrivé 📰 ».
5. Relie la sortie au bloc **Time await**.

Enregistre, puis **Start**. Autorise Automate à **s'exécuter en arrière-plan** et désactive pour lui l'**optimisation de la batterie** (Paramètres Android → Applis → Automate → Batterie → **Non restreinte**), sinon Android peut l'endormir la nuit.

### Lire le journal

Dans **ReadEra**, ajoute le dossier `Download/SinaJournal` : chaque matin, le nouveau numéro y apparaît. Avec **Moon+ Reader** ou **Lithium**, c'est le même principe : indique le dossier `Download/SinaJournal`.

> ℹ️ **Google Play Livres** n'importe pas automatiquement les fichiers d'un dossier. Préfère ReadEra ou Moon+ Reader.

---

## 8. Autre solution : cron-job.org

Pour **lancer** le journal sans dépendre du téléphone (pratique sur Android, ou si ton iPhone est souvent sans réseau à 7h) :

1. Crée un compte gratuit sur [cron-job.org](https://cron-job.org).
2. **Create cronjob** :
   - **URL** : `https://api.github.com/repos/TON-PSEUDO/NOM-DU-DEPOT/actions/workflows/journal.yml/dispatches`
   - **Schedule** : tous les jours à **07:00**, fuseau **Africa/Algiers** (ou le tien).
3. Onglet **Advanced** :
   - **Request method** : `POST`
   - **Headers** : `Authorization` = `Bearer TON_JETON` et `Accept` = `application/vnd.github+json`
   - **Request body** : `{"ref":"main"}`
4. Enregistre, puis utilise **Test run** une fois pour vérifier (un nouveau « Journal du matin » doit apparaître dans **Actions**).

Avec cette méthode, le téléphone n'a plus qu'à **télécharger** le journal à 8h (automatisation 2 sur iPhone, flux 2 sur Android).

---

## 9. Personnaliser

Tout se règle dans le bloc **CONFIGURATION**, en haut de `journal.py`. Pour le modifier depuis le site GitHub : ouvre le fichier → ✏️ (**Edit**) → modifie → **Commit changes**.

| Réglage | Rôle |
|---|---|
| `TITRE`, `DEVISE`, `EDITION` | Nom du journal (partie grasse, partie italique), devise, édition |
| `DATE_PREMIER_NUMERO` | Date du n° 1, pour numéroter les éditions |
| `UTILISER_CLAUDE` | `True` = version Claude (si la clé est présente) ; `False` = version gratuite |
| `MODELE` | `claude-sonnet-5-5` (par défaut) ou `claude-haiku-4-5` (2 fois moins cher) |
| `EFFORT` | `low` (économique), `medium` ou `high` (plus soigné, plus cher) |
| `VILLE`, `FUSEAU` | Météo et horaires de prière |
| `METHODE_PRIERE` | 19 = Algérie · 12 = UOIF (France) · 3 = Ligue islamique mondiale · 21 = Maroc · 18 = Tunisie |
| `NIVEAU_ANGLAIS`, `NIVEAU_ESPAGNOL` | Niveau des leçons |
| `SOURCES` | Les flux RSS de chaque rubrique |
| `RUBRIQUES` | Nombre d'articles développés et ligne éditoriale de chaque rubrique |

**Changer de ville** (coordonnées : appui long sur un lieu dans Google Maps) :

| Ville | lat | lon | FUSEAU |
|---|---|---|---|
| Alger | 36.75 | 3.06 | Africa/Algiers |
| Oran | 35.70 | -0.63 | Africa/Algiers |
| Constantine | 36.37 | 6.61 | Africa/Algiers |
| Tunis | 36.81 | 10.18 | Africa/Tunis |
| Casablanca | 33.57 | -7.59 | Africa/Casablanca |
| Paris | 48.86 | 2.35 | Europe/Paris |

---

## 10. Coûts

| Élément | Coût |
|---|---|
| GitHub (dépôt public, Actions, Pages) | Gratuit |
| Météo, prières, verset, échecs, tableau, Wikipédia | Gratuit |
| Raccourcis / Automate / ReadEra / cron-job.org | Gratuit |
| **Version gratuite** | **0 €** |
| **Version Claude** (Sonnet 5.5, effort `low`) | Environ **0,20-0,25 $ par journal**, soit ~7 $/mois (mesuré) |
| Version Claude avec `MODELE = "claude-haiku-4-5"` | Environ 3-4 $/mois (estimation) |

⚠️ **Chaque fabrication est payée.** Un lancement manuel (bouton ▶︎ du raccourci de 7h, **Run workflow** sur GitHub, **Test run** sur cron-job.org) refait un journal complet, même si celui du jour existe déjà. Pour simplement relire le journal, utilise le raccourci de **8h**, qui est gratuit.

Suivi des dépenses : [console.anthropic.com](https://console.anthropic.com) → **Usage**.

---

## 11. Sécurité

- **Ta clé Claude** est rangée dans les **Secrets GitHub** : chiffrée et invisible, même dans un dépôt public (les journaux d'exécution affichent `***`). Aucun fichier du projet ne la contient.
- **Ton jeton GitHub** reste dans ton téléphone (ou sur cron-job.org). Il ne peut que lancer ou annuler ton journal.
- Si l'un des deux a fuité : supprime-le (console Anthropic ou réglages GitHub), crée-en un nouveau et remplace-le.
- Le journal est publié à une adresse publique, mais que personne ne connaît, et il ne contient rien de personnel.

---

## 12. Dépannage

**❌ Croix rouge dans l'onglet Actions** → touche-la, puis touche l'étape en rouge et lis le message.

| Message | Cause | Solution |
|---|---|---|
| `Get Pages site failed` / `Not Found` (étape *deploy*) | GitHub Pages pas activé | Étape 3 : Source = **GitHub Actions** |
| `Branch "…" is not allowed to deploy` | Lancé depuis une autre branche que `main` | Lance depuis `main` |
| `not scoped to a workspace` | Clé Claude créée sans espace de travail | Recrée la clé dans un Workspace |
| `authentication_error` / `invalid x-api-key` | Clé Claude absente ou fausse | Refais la section 4 |
| `credit balance is too low` | Plus de crédit Claude | Recharge sur la console (le journal sort quand même, en version gratuite) |

**📭 Pas de nouveau journal le matin**
1. Ouvre `https://TON-PSEUDO.github.io/NOM-DU-DEPOT/date.txt` : la date affichée est celle du dernier journal publié.
2. Onglet **Actions** : y a-t-il un lancement vers 7h00 ? Si non, l'automatisation de 7h ne s'est pas exécutée (réseau, jeton, batterie sur Android).
3. Teste le lancement à la main (▶︎ sur iPhone, *Test run* sur cron-job.org) et regarde si un lancement apparaît dans **Actions**.

**🔁 Le raccourci de 7h répond une erreur**
- `401` / `Bad credentials` : le jeton est faux ou expiré. Vérifie `Bearer ` suivi d'une espace.
- `404` : l'adresse ou le nom du dépôt est faux, ou le jeton n'a pas accès à ce dépôt.
- `403` : la permission **Actions : Read and write** manque sur le jeton.
- `422` : le corps n'est pas `{"ref":"main"}`, ou la branche ne s'appelle pas `main`.

**📄 Le journal n'a pas de textes rédigés** → la clé Claude n'est pas lue : le secret doit s'appeler exactement `ANTHROPIC_API_KEY`. Dans les journaux de l'étape `python journal.py`, chaque rédaction réussie affiche `✓ Claude : …`.

**📭 Une rubrique « indisponible »** → sa source RSS est en panne ou bloque GitHub. Le reste du journal paraît quand même. Si ça dure, remplace le flux dans `SOURCES`.

**🕌 Horaires légèrement différents de ceux de la mosquée** → c'est normal (arrondis, marges). Essaie une autre `METHODE_PRIERE`. La date hégirienne est calculée et peut avoir un jour d'écart avec l'annonce officielle du croissant.

**💤 Inactivité** : GitHub met en pause les lancements automatiques d'un dépôt resté 60 jours sans modification (tu reçois un e-mail). Le lancement par le téléphone continue de marcher, mais tu peux réactiver le workflow dans **Actions**.

---

*Mise en page inspirée de [Signal Matin](https://github.com/sosoj92/signal-matin) (licence MIT). Œuvres d'art : Art Institute of Chicago (domaine public). Puzzles : Lichess. Versets : AlQuran Cloud (trad. Hamidullah). Prières : Aladhan. Météo : Open-Meteo. « Ce jour-là » : Wikipédia.*
