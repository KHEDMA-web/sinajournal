# Installation — Mon Journal du Matin

## 1. Le dépôt GitHub
Le dépôt est `KHEDMA-web/sinajournal` (il doit être **public** pour GitHub Pages gratuit).
Il contient : `journal.py`, `requirements.txt` et `.github/workflows/journal.yml`
(le chemin du dossier `.github/workflows/` est important).

## 2. La clé API Claude
1. Crée une clé sur https://console.anthropic.com (quelques centimes par journal).
2. Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**
   - Nom : `ANTHROPIC_API_KEY`
   - Valeur : ta clé

Sans clé, le journal est quand même généré, mais sans résumés ni leçons de langue.

## 3. GitHub Pages
**Settings → Pages → Source : GitHub Actions**.

## 4. Premier test
Onglet **Actions → Journal du matin → Run workflow**.
Après 1-2 minutes, ton journal est ici :
`https://khedma-web.github.io/sinajournal/journal.epub`

## 5. Le Raccourci iPhone (livraison à 8h)
App **Raccourcis → Automatisation → + → Heure de la journée**
- 08:00, Quotidien, **Exécuter immédiatement** (pas de confirmation)
- Actions :
  1. **URL** → `https://khedma-web.github.io/sinajournal/journal.epub`
  2. **Obtenir le contenu de l'URL**
  3. **Définir le nom** → `Journal.epub`
  4. **Ajouter à Livres** (parfois nommé « Enregistrer le PDF dans Livres » ; ça marche aussi pour les EPUB)

## Personnaliser
Tout est en haut de `journal.py` :
- `TITRE`, `DEVISE`, `EDITION` : le nom du journal (partie grasse + partie italique) ;
- `VILLE`, `FUSEAU` : la météo et les horaires de prière ;
- `METHODE_PRIERE` : méthode de calcul (19 = Algérie ; 12 = UOIF France, 3 = Ligue islamique mondiale) ;
- `NIVEAU_ANGLAIS`, `NIVEAU_ESPAGNOL` : le niveau des leçons ;
- `MODELE`, `EFFORT` : le modèle Claude et le soin apporté à la rédaction ;
- `DATE_PREMIER_NUMERO` : le point de départ de la numérotation ;
- `RUBRIQUES` : le nombre d’articles développés et la ligne éditoriale de chaque rubrique ;
- `SOURCES` : les flux RSS de chaque rubrique (une source en panne n'empêche pas le reste).

Mise en page inspirée de Signal Matin (github.com/sosoj92/signal-matin, licence MIT).

## Bon à savoir
- GitHub peut lancer le script avec 10 à 30 min de retard, d'où le lancement à 7h30 pour une lecture à 8h.
- GitHub met en pause les tâches planifiées après 60 jours sans activité sur le dépôt : un petit commit de temps en temps suffit.
- Le dépôt étant public, le lien du journal l'est aussi (mais personne ne le connaît).

## Horaires de prière
Calculés par l'API Aladhan. La date hégirienne est calculée et peut différer d'un jour de l'annonce officielle (observation du croissant) : en cas de doute pour le Ramadan ou l'Aïd, fie-toi au ministère.
