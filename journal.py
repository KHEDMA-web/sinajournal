"""Sina Journal — génère chaque matin un petit quotidien personnel au format EPUB.

Mise en page inspirée de Signal Matin (github.com/sosoj92/signal-matin, licence MIT).
"""

import datetime as dt
import html
import io
import json
import os
import re
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zoneinfo import ZoneInfo

import chess
import chess.pgn
import chess.svg
import feedparser
import requests
from ebooklib import epub

# ═════════════════════════════════ CONFIGURATION ═════════════════════════════════

TITRE = ("Sina", "Journal")          # partie grasse, partie italique
DEVISE = "Un matin informé, sans commencer par défiler."
EDITION = "Édition d'Alger"
DATE_PREMIER_NUMERO = dt.date(2026, 9, 29)   # pour numéroter les éditions
MODELE = "claude-sonnet-5-5"          # modèle Claude utilisé
EFFORT = "low"                        # low = moins cher ; medium / high = plus soigné
VILLE = {"nom": "Alger", "lat": 36.75, "lon": 3.06}
FUSEAU = "Africa/Algiers"
METHODE_PRIERE = 19                   # 19 = Algérie ; 12 = UOIF France ; 3 = Ligue islamique mondiale
NIVEAU_ANGLAIS = "B1 (intermédiaire)"
NIVEAU_ESPAGNOL = "A2 (débutant avancé)"

# Flux RSS par rubrique : une source en panne n'empêche pas le reste.
SOURCES = {
    "Monde": [
        "https://www.france24.com/fr/rss",
        "https://www.lemonde.fr/international/rss_full.xml",
    ],
    "Algérie": [
        "https://www.tsa-algerie.com/feed/",
        "https://www.algerie360.com/feed/",
    ],
    "Économie": [
        "https://www.lemonde.fr/economie/rss_full.xml",
    ],
    "Tech & IA": [
        "https://www.actuia.com/feed/",
        "https://www.journaldugeek.com/feed/",
        "https://www.blogdumoderateur.com/feed/",
    ],
    "Sciences": [
        "https://www.futura-sciences.com/rss/actualites.xml",
        "https://theconversation.com/fr/articles.atom",
    ],
    "Culture": [
        "https://www.lemonde.fr/culture/rss_full.xml",
    ],
    "Sport": [
        "https://www.dzfoot.com/feed",
        "https://www.algerie360.com/category/sport/feed/",
        "https://www.footmercato.net/flux-rss",
    ],
}

# Rubriques d'actualité : (nombre d'articles développés, consigne éditoriale)
RUBRIQUES = {
    "Monde": (3, "Les grands faits internationaux du jour."),
    "Algérie": (2, "Politique, économie et société algériennes."),
    "Économie": (2, "Économie, entreprises et marchés."),
    "Tech & IA": (2, "Donne la priorité à l'intelligence artificielle, puis au reste de la tech."),
    "Sciences": (2, "Des découvertes scientifiques, expliquées simplement pour un non-spécialiste."),
    "Culture": (2, "Livres, cinéma, musique, expositions."),
    "Sport": (2, "Le football algérien d'abord (sélection, championnat, joueurs algériens), "
                "puis le football européen et les autres sports."),
}
BREVES = 4

# ═════════════════════════════════════ OUTILS ═════════════════════════════════════

SORTIE = Path("dist")
HTTP = {"User-Agent": "SinaJournal/1.0 (+https://github.com/KHEDMA-web/sinajournal)"}

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
MOIS_HEGIRE = ["Mouharram", "Safar", "Rabi' al-awwal", "Rabi' ath-thani",
               "Joumada al-oula", "Joumada ath-thania", "Rajab", "Cha'bane",
               "Ramadan", "Chawwal", "Dhou al-qi'da", "Dhou al-hijja"]
PRIERES = [("Fajr", "Sobh"), ("Sunrise", "Chourouq"), ("Dhuhr", "Dohr"),
           ("Asr", "Asr"), ("Maghrib", "Maghreb"), ("Isha", "Icha")]
METEO_CODES = {
    0: "Ciel dégagé", 1: "Plutôt dégagé", 2: "Partiellement nuageux", 3: "Couvert",
    45: "Brouillard", 48: "Brouillard givrant", 51: "Bruine légère", 53: "Bruine",
    55: "Bruine dense", 61: "Pluie faible", 63: "Pluie", 65: "Forte pluie",
    71: "Neige faible", 73: "Neige", 75: "Forte neige", 80: "Averses",
    81: "Averses", 82: "Fortes averses", 95: "Orage", 96: "Orage et grêle",
    99: "Orage et grêle",
}

SYSTEME = ("Tu es le rédacteur en chef de Sina Journal, un petit quotidien francophone "
           "lu chaque matin à Alger. Ton style est clair, sobre et précis. Pour l'actualité, "
           "tu t'en tiens strictement aux faits présents dans les dépêches fournies.")

_client = None
_claude_simultanes = threading.Semaphore(3)  # ménage les limites de débit de l'API


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def nettoyer(texte, limite=600):
    texte = html.unescape(re.sub(r"<[^>]+>", " ", texte or ""))
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte if len(texte) <= limite else texte[:limite].rsplit(" ", 1)[0] + "…"


def e(texte):
    return html.escape(str(texte or ""), quote=True)


def get_json(url, **params):
    r = requests.get(url, headers=HTTP, timeout=20, params=params or None)
    r.raise_for_status()
    return r.json()


def lire_flux(url):
    try:
        r = requests.get(url, headers=HTTP, timeout=20)
        r.raise_for_status()
        flux = feedparser.parse(r.content)
    except Exception as err:  # une source en panne ne doit rien bloquer
        log(f"  ✗ {url} : {err}")
        return []
    source = nettoyer(flux.feed.get("title", ""), 60) or url
    articles = []
    for entree in flux.entries:
        date = entree.get("published_parsed") or entree.get("updated_parsed")
        articles.append({
            "titre": nettoyer(entree.get("title", ""), 200),
            "resume": nettoyer(entree.get("summary", "")),
            "lien": entree.get("link", ""),
            "source": source,
            "date": dt.datetime(*date[:6], tzinfo=dt.timezone.utc) if date else None,
        })
    log(f"  ✓ {url} : {len(articles)} articles")
    return articles


def depeches(rubrique, maintenant, nombre=12):
    limite = maintenant - dt.timedelta(hours=36)
    vus, articles = set(), []
    for url in SOURCES.get(rubrique, []):
        for a in lire_flux(url):
            cle = a["titre"].lower()
            if not a["titre"] or cle in vus or (a["date"] and a["date"] < limite):
                continue
            vus.add(cle)
            articles.append(a)
    articles.sort(key=lambda a: a["date"] or limite, reverse=True)
    return articles[:nombre]


def texte_depeches(articles):
    return "\n".join(f"{i}. [{a['source']}] {a['titre']}\n   {a['resume']}"
                     for i, a in enumerate(articles, 1))


def objet(proprietes):
    """Schéma JSON d'un objet dont tous les champs sont obligatoires."""
    return {"type": "object", "properties": proprietes,
            "required": list(proprietes), "additionalProperties": False}


def liste(items):
    return {"type": "array", "items": items}


TEXTE = {"type": "string"}


def claude(nom, consigne, schema):
    """Appelle Claude et renvoie le JSON demandé, ou None (pas de clé, erreur…)."""
    if _client is None:
        return None
    import anthropic

    with _claude_simultanes:
        try:
            reponse = _client.beta.messages.create(
                model=MODELE,
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                extra_body={"fallbacks": "default"},
                output_config={"effort": EFFORT,
                               "format": {"type": "json_schema", "schema": schema}},
                system=SYSTEME,
                messages=[{"role": "user", "content": consigne}],
            )
        except anthropic.APIConnectionError as err:
            log(f"  ✗ Claude ({nom}) injoignable : {err}")
            return None
        except anthropic.APIStatusError as err:
            log(f"  ✗ Claude ({nom}) erreur {err.status_code} : {err.message}")
            return None
    if reponse.stop_reason in ("refusal", "max_tokens"):
        log(f"  ✗ Claude ({nom}) : réponse inutilisable ({reponse.stop_reason})")
        return None
    texte = next((b.text for b in reponse.content if b.type == "text"), "")
    try:
        resultat = json.loads(texte)
    except json.JSONDecodeError:
        log(f"  ✗ Claude ({nom}) : réponse illisible")
        return None
    log(f"  ✓ Claude : {nom}")
    return resultat


# ════════════════════════════════════ CONTENUS ════════════════════════════════════

def donnees_meteo(jour):
    try:
        j = get_json("https://api.open-meteo.com/v1/forecast",
                     latitude=VILLE["lat"], longitude=VILLE["lon"], timezone=FUSEAU,
                     start_date=jour.isoformat(), end_date=jour.isoformat(),
                     daily="weathercode,temperature_2m_max,temperature_2m_min,"
                           "precipitation_probability_max,windspeed_10m_max")["daily"]
        return {
            "ciel": METEO_CODES.get(j["weathercode"][0], "—"),
            "min": round(j["temperature_2m_min"][0]),
            "max": round(j["temperature_2m_max"][0]),
            "pluie": j["precipitation_probability_max"][0],
            "vent": round(j["windspeed_10m_max"][0]),
        }
    except Exception as err:
        log(f"  ✗ Météo : {err}")
        return None


def donnees_priere(jour):
    try:
        data = get_json(f"https://api.aladhan.com/v1/timings/{jour:%d-%m-%Y}",
                        latitude=VILLE["lat"], longitude=VILLE["lon"],
                        method=METHODE_PRIERE)["data"]
    except Exception as err:
        log(f"  ✗ Prières : {err}")
        return None
    t = data["timings"]
    vendredi = jour.weekday() == 4
    horaires = []
    for cle, nom in PRIERES:
        if cle == "Dhuhr" and vendredi:
            nom = "Joumou'a"
        horaires.append((nom, t[cle][:5]))
    hijri = data["date"]["hijri"]
    mois = int(hijri["month"]["number"])
    return {
        "horaires": horaires,
        "hegire": f"{int(hijri['day'])} {MOIS_HEGIRE[mois - 1]} {hijri['year']}",
        "vendredi": vendredi,
        "ramadan": ({"jour": int(hijri["day"]), "imsak": t["Imsak"][:5],
                     "iftar": t["Maghrib"][:5]} if mois == 9 else None),
    }


def donnees_verset(jour):
    numero = (jour.toordinal() * 7919) % 6236 + 1   # un verset différent chaque jour
    try:
        ar, fr = get_json(f"https://api.alquran.cloud/v1/ayah/{numero}/editions/"
                          "quran-uthmani,fr.hamidullah")["data"]
    except Exception as err:
        log(f"  ✗ Verset : {err}")
        return None
    return {"arabe": ar["text"], "francais": fr["text"],
            "reference": f"Sourate {ar['surah']['englishName']} ({ar['surah']['number']}), "
                         f"verset {ar['numberInSurah']}"}


PIECES_FR = str.maketrans({"K": "R", "Q": "D", "R": "T", "B": "F", "N": "C"})


def donnees_echecs():
    try:
        j = get_json("https://lichess.org/api/puzzle/daily")
        puzzle = j["puzzle"]
        if puzzle.get("fen"):
            plateau = chess.Board(puzzle["fen"])
        else:
            partie = chess.pgn.read_game(io.StringIO(j["game"]["pgn"]))
            plateau = partie.end().board()
        depart = plateau.copy()
        coups = []
        for i, uci in enumerate(puzzle["solution"]):
            coup = chess.Move.from_uci(uci)
            san = plateau.san(coup).translate(PIECES_FR)
            if plateau.turn == chess.WHITE:
                coups.append(f"{plateau.fullmove_number}. {san}")
            elif i == 0:
                coups.append(f"{plateau.fullmove_number}… {san}")
            else:
                coups.append(san)
            plateau.push(coup)
        dernier = puzzle.get("lastMove")
        svg = chess.svg.board(depart, flipped=depart.turn == chess.BLACK, size=360,
                              lastmove=chess.Move.from_uci(dernier) if dernier else None)
        return {
            "svg": svg,
            "trait": "Les Blancs jouent" if depart.turn == chess.WHITE else "Les Noirs jouent",
            "solution": " ".join(coups),
            "difficulte": puzzle.get("rating"),
            "lien": f"https://lichess.org/training/{puzzle['id']}",
        }
    except Exception as err:
        log(f"  ✗ Échecs : {err}")
        return None


def donnees_ce_jour(jour):
    try:
        j = get_json(f"https://fr.wikipedia.org/api/rest_v1/feed/onthisday/all/"
                     f"{jour:%m}/{jour:%d}")
    except Exception as err:
        log(f"  ✗ Ce jour-là : {err}")
        return None

    def extraire(cle, nombre):
        items = [(x["year"], nettoyer(x["text"], 300)) for x in j.get(cle, [])
                 if "year" in x and x.get("text")]
        return sorted(items[:nombre])

    evenements = extraire("selected", 6) or extraire("events", 6)
    naissances = extraire("births", 4)
    if not evenements and not naissances:
        return None
    return {"evenements": evenements, "naissances": naissances}


SCHEMA_ARTICLE = objet({"titre": TEXTE, "chapeau": TEXTE, "texte": TEXTE, "source": TEXTE})
SCHEMA_BREVE = objet({"titre": TEXTE, "texte": TEXTE})
SCHEMA_RUBRIQUE = objet({"articles": liste(SCHEMA_ARTICLE), "breves": liste(SCHEMA_BREVE)})


def donnees_actu(nom, articles, date_texte):
    if not articles:
        return {"indisponible": True}
    developpes, consigne = RUBRIQUES[nom]
    ia = claude(nom, f"""Nous sommes le {date_texte}. Rubrique « {nom} » de Sina Journal.
{consigne}

Dépêches disponibles :
{texte_depeches(articles)}

Rédige en français :
- "articles" : les {developpes} sujets les plus importants, chacun avec un titre de journal,
  un chapeau d'une phrase, un texte de 2 ou 3 paragraphes séparés par une ligne vide
  (150 à 220 mots au total), et le nom de la source.
- "breves" : jusqu'à {BREVES} autres sujets en une ou deux phrases chacun.
N'invente aucun fait, chiffre ou citation absent des dépêches.""", SCHEMA_RUBRIQUE)
    if ia:
        return ia
    # Version simplifiée (sans clé API) : titres et extraits bruts.
    return {
        "articles": [{"titre": a["titre"], "chapeau": "", "texte": a["resume"],
                      "source": a["source"]} for a in articles[:developpes]],
        "breves": [{"titre": a["titre"], "texte": ""}
                   for a in articles[developpes:developpes + BREVES]],
    }


def donnees_une(toutes, date_texte):
    if not toutes:
        return None
    return claude("la une", f"""Nous sommes le {date_texte}. Voici les dépêches du matin :
{texte_depeches(toutes)}

Prépare la une de Sina Journal, en français :
- "manchette" : le sujet principal du jour (titre fort + chapeau de 2 phrases).
- "essentiel" : 4 phrases qui résument les autres faits marquants.
- "question_du_matin" : une question ouverte pour réfléchir en buvant son café.
- "mot_du_jour" : un mot français riche ou peu courant, avec sa définition.
- "chiffre_du_jour" : un chiffre tiré des dépêches, avec une phrase d'explication.
- "intention_du_jour" : une courte intention positive et concrète pour la journée.""",
        objet({
            "manchette": objet({"titre": TEXTE, "chapeau": TEXTE}),
            "essentiel": liste(TEXTE),
            "question_du_matin": TEXTE,
            "mot_du_jour": objet({"mot": TEXTE, "definition": TEXTE}),
            "chiffre_du_jour": objet({"chiffre": TEXTE, "explication": TEXTE}),
            "intention_du_jour": TEXTE,
        }))


def donnees_dossier(toutes, date_texte):
    if not toutes:
        return None
    return claude("le dossier", f"""Nous sommes le {date_texte}. Dépêches du jour :
{texte_depeches(toutes)}

Choisis UN sujet de ces dépêches qui mérite d'être expliqué en profondeur et rédige
« Le dossier du jour » : un titre, un sous-titre, 4 à 6 paragraphes qui donnent le contexte,
les enjeux et ce qui peut se passer ensuite (tu peux t'appuyer sur tes connaissances
générales pour le contexte, mais pas inventer de faits récents), puis 3 à 5 points
« À retenir ».""",
        objet({"titre": TEXTE, "sous_titre": TEXTE, "paragraphes": liste(TEXTE),
               "a_retenir": liste(TEXTE)}))


def lecon(langue, niveau, actus, date_texte):
    return claude(f"leçon {langue}", f"""Nous sommes le {date_texte}. Crée une leçon de {langue}
de niveau {niveau} pour un francophone, inspirée d'un de ces sujets d'actualité :
{actus}

- "theme" : le thème (en français).
- "expression" : une expression idiomatique en {langue} et son explication en français.
- "vocabulaire" : 6 mots (mot en {langue}, traduction, phrase d'exemple en {langue}).
- "texte" : un texte de 80 à 120 mots en {langue} ; "traduction" : sa traduction française.
- "grammaire" : un point de grammaire utile à ce niveau, expliqué en français, avec
  3 exemples en {langue}.
- "exercices" : 4 petits exercices (textes à trous, traduction…) ; "corrige" : les
  réponses dans le même ordre.""",
        objet({
            "theme": TEXTE,
            "expression": objet({"expression": TEXTE, "explication": TEXTE}),
            "vocabulaire": liste(objet({"mot": TEXTE, "traduction": TEXTE, "exemple": TEXTE})),
            "texte": TEXTE,
            "traduction": TEXTE,
            "grammaire": objet({"point": TEXTE, "explication": TEXTE,
                                "exemples": liste(TEXTE)}),
            "exercices": liste(TEXTE),
            "corrige": liste(TEXTE),
        }))


def donnees_arabe(date_texte):
    return claude("arabe & darija", f"""Nous sommes le {date_texte}. Pour la rubrique
« Arabe & darija », propose :
- un mot en arabe standard (écrit en arabe avec voyelles), sa translittération, sa
  traduction française, une phrase d'exemple en arabe et sa traduction ;
- une expression de darija algérienne courante (en lettres latines comme on l'écrit à
  Alger, et en arabe), son sens et une situation où on l'utilise.""",
        objet({
            "mot": TEXTE, "translitteration": TEXTE, "traduction": TEXTE,
            "exemple": TEXTE, "exemple_traduction": TEXTE,
            "darija": TEXTE, "darija_arabe": TEXTE, "darija_sens": TEXTE,
            "darija_usage": TEXTE,
        }))


def donnees_quiz(actus, date_texte):
    return claude("quiz", f"""Nous sommes le {date_texte}. Crée un quiz de 5 questions à choix
multiples (4 choix chacune) : 2 questions sur ces actualités du jour, 3 de culture générale
(histoire, géographie, sciences, Algérie, monde arabe…).
{actus}
Pour chaque question : "question", "choix" (4 réponses, sans lettre devant),
"reponse" (la lettre A, B, C ou D) et "explication" (une phrase).""",
        objet({"questions": liste(objet({"question": TEXTE, "choix": liste(TEXTE),
                                          "reponse": TEXTE, "explication": TEXTE}))}))


def donnees_citations(date_texte):
    return claude("citations", f"""Nous sommes le {date_texte}. Pour la rubrique
« Citations & lectures », propose :
- "citations" : 3 citations authentiques et vérifiables (texte en français + auteur),
  d'horizons variés ;
- "extrait" : un court extrait (80 à 150 mots) d'un classique du domaine public, cité
  fidèlement (en traduction française si besoin), avec l'œuvre et l'auteur ;
- "idee" : une idée concrète à appliquer aujourd'hui, avec un titre et 2 ou 3 phrases.""",
        objet({
            "citations": liste(objet({"texte": TEXTE, "auteur": TEXTE})),
            "extrait": objet({"oeuvre": TEXTE, "auteur": TEXTE, "texte": TEXTE}),
            "idee": objet({"titre": TEXTE, "texte": TEXTE}),
        }))


# ═══════════════════════════════════ MISE EN PAGE ═══════════════════════════════════

CSS = """
body { font-family: Georgia, "Times New Roman", serif; line-height: 1.5; margin: 0 4%;
       color: #111; }
.masthead { text-align: center; border-bottom: 3px double #111; padding-bottom: .4em;
            margin-bottom: .8em; }
.masthead h1 { font-size: 2.8em; margin: .1em 0 0; line-height: 1.1; }
.masthead h1 b { font-weight: 900; }
.masthead h1 i { font-weight: 400; }
.devise { font-style: italic; font-size: .9em; margin: .2em 0 .5em; }
.bandeau { font-size: .72em; text-transform: uppercase; letter-spacing: .1em;
           border-top: 1px solid #111; border-bottom: 1px solid #111; padding: .3em 0; }
.manchette { font-size: 1.7em; line-height: 1.15; margin: .6em 0 .2em; }
h2 { font-size: 1em; text-transform: uppercase; letter-spacing: .14em;
     border-top: 3px solid #111; border-bottom: 1px solid #111; padding: .2em 0;
     margin: 1.6em 0 .8em; }
h3 { font-size: 1.25em; line-height: 1.2; margin: 1.1em 0 .2em; }
h4 { font-size: .8em; text-transform: uppercase; letter-spacing: .1em; margin: 1.2em 0 .3em; }
.chapeau { font-weight: bold; margin: .2em 0 .5em; }
.source { font-size: .72em; color: #666; text-transform: uppercase; letter-spacing: .06em; }
p.lettrine::first-letter { float: left; font-size: 3.2em; line-height: .8;
                           padding: .08em .08em 0 0; font-weight: bold; }
.filet { border: 0; border-top: 1px solid #111; margin: 1.2em 30%; }
.encadre { border: 1px solid #111; padding: .5em .8em; margin: .9em 0; }
.encadre h4 { margin-top: 0; }
.breve { margin: .4em 0; }
table { width: 100%; border-collapse: collapse; }
td { padding: .15em .3em; border-bottom: 1px dotted #999; vertical-align: top; }
td.h { text-align: right; }
.ar { direction: rtl; text-align: right; font-size: 1.3em; line-height: 1.8; }
.vo { font-style: italic; }
.note { font-size: .78em; color: #555; }
.centre { text-align: center; }
ol.choix { list-style-type: upper-alpha; }
a { color: inherit; }
"""


def paragraphes(blocs, lettrine=True):
    """Paragraphes HTML, le premier avec une lettrine."""
    if isinstance(blocs, str):
        blocs = re.split(r"\n\s*\n", blocs)
    blocs = [b.strip() for b in blocs if b and b.strip()]
    sortie = []
    for i, b in enumerate(blocs):
        classe = ' class="lettrine"' if lettrine and i == 0 else ""
        sortie.append(f"<p{classe}>{e(b)}</p>")
    return "".join(sortie)


def page_une(c):
    pri, met, une, verset = c["priere"], c["meteo"], c["une"], c["verset"]
    hegire = f" · {e(pri['hegire'])}" if pri else ""
    b = [f"""<div class="masthead">
<h1><b>{e(TITRE[0])}</b> <i>{e(TITRE[1])}</i></h1>
<p class="devise">{e(DEVISE)}</p>
<div class="bandeau">N° {c['numero']} · {e(c['date_texte'])}{hegire} · {e(EDITION)}</div>
</div>"""]
    if une:
        m = une["manchette"]
        b.append(f"<h3 class='manchette'>{e(m['titre'])}</h3>"
                 f"<p class='chapeau'>{e(m['chapeau'])}</p>")
        if une["essentiel"]:
            b.append("<h4>L'essentiel</h4>" + "".join(
                f"<p class='breve'>■ {e(p)}</p>" for p in une["essentiel"]))
    if pri:
        lignes = "".join(f"<tr><td>{e(n)}</td><td class='h'>{h}</td></tr>"
                         for n, h in pri["horaires"])
        extra = ""
        if pri["ramadan"]:
            r = pri["ramadan"]
            extra += (f"<p><b>Ramadan · jour {r['jour']} · Imsak {r['imsak']} · "
                      f"Iftar {r['iftar']}</b></p>")
        if pri["vendredi"]:
            extra += "<p>Joumou'a moubaraka. Pense à la lecture de la sourate Al-Kahf.</p>"
        b.append(f"""<div class="encadre"><h4>Prières — {e(VILLE['nom'])}</h4>
<table>{lignes}</table>{extra}
<p class="note">Date hégirienne calculée : elle peut différer d'un jour de l'annonce
officielle.</p></div>""")
    if met:
        b.append(f"""<div class="encadre"><h4>Météo — {e(VILLE['nom'])}</h4>
<p>{e(met['ciel'])}, {met['min']}° / {met['max']}°. Pluie : {met['pluie']} %.
Vent : {met['vent']} km/h.</p></div>""")
    if verset:
        b.append(f"""<div class="encadre"><h4>Verset du jour</h4>
<p class="ar" lang="ar">{e(verset['arabe'])}</p>
<p class="vo">{e(verset['francais'])}</p>
<p class="note">{e(verset['reference'])} — trad. Hamidullah</p></div>""")
    if une:
        mot, chiffre = une["mot_du_jour"], une["chiffre_du_jour"]
        b.append(f"""<div class="encadre"><h4>Question du matin</h4>
<p>{e(une['question_du_matin'])}</p></div>
<div class="encadre"><h4>Mot du jour</h4><p><b>{e(mot['mot'])}</b> — {e(mot['definition'])}</p></div>
<div class="encadre"><h4>Chiffre du jour</h4><p><b>{e(chiffre['chiffre'])}</b> —
{e(chiffre['explication'])}</p></div>
<div class="encadre"><h4>Intention du jour</h4><p>{e(une['intention_du_jour'])}</p></div>""")
    b.append("<h4>Sommaire</h4>" + "".join(
        f"<p class='breve'>{e(t)}</p>" for t in c["sommaire"]))
    return "\n".join(b)


def page_actu(nom, d):
    b = [f"<h2>{e(nom)}</h2>"]
    if d.get("indisponible"):
        b.append("<p class='note'>Rubrique indisponible ce matin : "
                 "les sources n'ont pas répondu.</p>")
        return "\n".join(b)
    for i, a in enumerate(d["articles"]):
        if i:
            b.append("<hr class='filet'/>")
        b.append(f"<h3>{e(a['titre'])}</h3>")
        if a["source"]:
            b.append(f"<p class='source'>{e(a['source'])}</p>")
        if a["chapeau"]:
            b.append(f"<p class='chapeau'>{e(a['chapeau'])}</p>")
        b.append(paragraphes(a["texte"]))
    if d["breves"]:
        breves = []
        for x in d["breves"]:
            suite = f" — {e(x['texte'])}" if x["texte"] else ""
            breves.append(f"<p class='breve'><b>{e(x['titre'])}</b>{suite}</p>")
        b.append("<h4>En bref</h4>" + "".join(breves))
    return "\n".join(b)


def page_dossier(d):
    retenir = "".join(f"<p class='breve'>■ {e(x)}</p>" for x in d["a_retenir"])
    return f"""<h2>Le dossier du jour</h2>
<h3 class="manchette">{e(d['titre'])}</h3><p class="chapeau">{e(d['sous_titre'])}</p>
{paragraphes(d['paragraphes'])}
<div class="encadre"><h4>À retenir</h4>{retenir}</div>"""


def page_lecon(titre, niveau, d):
    vocab = "".join(
        f"<tr><td><b>{e(v['mot'])}</b></td><td>{e(v['traduction'])}</td></tr>"
        f"<tr><td colspan='2' class='vo'>{e(v['exemple'])}</td></tr>"
        for v in d["vocabulaire"])
    g = d["grammaire"]
    exemples = "".join(f"<p class='vo breve'>• {e(x)}</p>" for x in g["exemples"])
    exercices = "".join(f"<p class='breve'>{i}. {e(x)}</p>"
                        for i, x in enumerate(d["exercices"], 1))
    corrige = "".join(f"<p class='breve'>{i}. {e(x)}</p>"
                      for i, x in enumerate(d["corrige"], 1))
    return f"""<h2>{e(titre)}</h2>
<p class="source">Niveau {e(niveau)} · {e(d['theme'])}</p>
<div class="encadre"><h4>Expression du jour</h4>
<p><b class="vo">{e(d['expression']['expression'])}</b></p>
<p>{e(d['expression']['explication'])}</p></div>
<h4>Vocabulaire</h4><table>{vocab}</table>
<h4>Texte</h4><p class="vo">{e(d['texte'])}</p><p>{e(d['traduction'])}</p>
<h4>Grammaire — {e(g['point'])}</h4><p>{e(g['explication'])}</p>{exemples}
<h4>Exercices</h4>{exercices}
<div class="encadre note"><h4>Corrigé</h4>{corrige}</div>"""


def page_arabe(d):
    return f"""<h2>Arabe &amp; darija</h2>
<div class="encadre"><h4>Le mot du jour</h4>
<p class="ar" lang="ar">{e(d['mot'])}</p>
<p><b>{e(d['translitteration'])}</b> — {e(d['traduction'])}</p>
<p class="ar" lang="ar">{e(d['exemple'])}</p><p class="vo">{e(d['exemple_traduction'])}</p></div>
<div class="encadre"><h4>L'expression algérienne</h4>
<p><b>{e(d['darija'])}</b></p><p class="ar" lang="ar">{e(d['darija_arabe'])}</p>
<p>{e(d['darija_sens'])}</p><p class="vo">{e(d['darija_usage'])}</p></div>"""


def page_jeux(echecs, quiz):
    b = ["<h2>Jeux de l'esprit</h2>"]
    if echecs:
        diff = f" · difficulté {echecs['difficulte']}" if echecs["difficulte"] else ""
        b.append(f"""<h4>Problème d'échecs du jour</h4>
<p class="centre"><img src="echecs.svg" alt="Position du problème d'échecs"
 style="width:90%;max-width:360px"/></p>
<p class="centre"><b>{echecs['trait']} et gagnent.</b></p>
<p class="note centre">Puzzle du jour Lichess{diff}</p>""")
    else:
        b.append("<p class='note'>Problème d'échecs indisponible ce matin.</p>")
    if quiz:
        b.append("<h4>Quiz du matin</h4>")
        for i, q in enumerate(quiz["questions"], 1):
            choix = "".join(f"<li>{e(x)}</li>" for x in q["choix"])
            b.append(f"<p><b>{i}. {e(q['question'])}</b></p><ol class='choix'>{choix}</ol>")
    b.append("<p class='note'>Les solutions sont à la fin du journal.</p>")
    return "\n".join(b)


def page_citations(d):
    cit = "".join(f"<p class='vo'>« {e(x['texte'])} »</p>"
                  f"<p class='source'>— {e(x['auteur'])}</p>" for x in d["citations"])
    x = d["extrait"]
    return f"""<h2>Citations &amp; lectures</h2>
{cit}
<div class="encadre"><h4>Extrait d'un classique</h4>
<p>{e(x['texte'])}</p><p class="source">{e(x['auteur'])}, <i>{e(x['oeuvre'])}</i></p></div>
<div class="encadre"><h4>Une idée à appliquer — {e(d['idee']['titre'])}</h4>
<p>{e(d['idee']['texte'])}</p></div>"""


def page_ce_jour(d, date_courte):
    b = [f"<h2>Ce jour-là — {e(date_courte)}</h2>"]
    for titre, items in (("Événements", d["evenements"]), ("Naissances", d["naissances"])):
        if items:
            b.append(f"<h4>{titre}</h4>" + "".join(
                f"<p class='breve'><b>{an}</b> — {e(t)}</p>" for an, t in items))
    b.append("<p class='note'>Source : Wikipédia.</p>")
    return "\n".join(b)


def page_solutions(echecs, quiz):
    b = ["<h2>Solutions</h2>"]
    if echecs:
        b.append(f"""<h4>Échecs</h4><p><b>{e(echecs['solution'])}</b></p>
<p class="note"><a href="{e(echecs['lien'])}">Rejouer le problème sur Lichess</a></p>""")
    if quiz:
        b.append("<h4>Quiz</h4>" + "".join(
            f"<p class='breve'><b>{i}. {e(q['reponse'])}</b> — {e(q['explication'])}</p>"
            for i, q in enumerate(quiz["questions"], 1)))
    return "\n".join(b)


# ═══════════════════════════════════ ASSEMBLAGE ═══════════════════════════════════

def chapitre(nom_fichier, titre, corps):
    c = epub.EpubHtml(title=titre, file_name=nom_fichier, lang="fr")
    c.content = f"<html><body>{corps}</body></html>"
    c.add_link(href="style.css", rel="stylesheet", type="text/css")
    return c


def main():
    global _client
    maintenant = dt.datetime.now(ZoneInfo(FUSEAU))
    jour = maintenant.date()
    date_texte = f"{JOURS[jour.weekday()]} {jour.day} {MOIS[jour.month - 1]} {jour.year}"
    numero = max(1, (jour - DATE_PREMIER_NUMERO).days + 1)
    log(f"Sina Journal n° {numero} — {date_texte}")

    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        _client = anthropic.Anthropic(max_retries=6)
    else:
        log("Pas de clé ANTHROPIC_API_KEY : version simplifiée (titres bruts, pas de leçons).")

    utc = maintenant.astimezone(dt.timezone.utc)
    with ThreadPoolExecutor(max_workers=10) as pool:
        # 1. Tout ce qui ne dépend de rien, en parallèle
        f_flux = {nom: pool.submit(depeches, nom, utc) for nom in RUBRIQUES}
        f_meteo = pool.submit(donnees_meteo, jour)
        f_priere = pool.submit(donnees_priere, jour)
        f_verset = pool.submit(donnees_verset, jour)
        f_echecs = pool.submit(donnees_echecs)
        f_ce_jour = pool.submit(donnees_ce_jour, jour)
        f_arabe = pool.submit(donnees_arabe, date_texte)
        f_citations = pool.submit(donnees_citations, date_texte)

        flux = {nom: f.result() for nom, f in f_flux.items()}
        toutes = [a for nom in ("Monde", "Algérie", "Économie", "Sciences", "Tech & IA")
                  for a in flux[nom][:6]]
        titres = "\n".join(f"- {a['titre']}" for a in toutes)

        # 2. Ce qui s'appuie sur les dépêches
        f_actu = {nom: pool.submit(donnees_actu, nom, flux[nom], date_texte)
                  for nom in RUBRIQUES}
        f_une = pool.submit(donnees_une, toutes, date_texte)
        f_dossier = pool.submit(donnees_dossier, toutes, date_texte)
        f_anglais = pool.submit(lecon, "anglais", NIVEAU_ANGLAIS, titres, date_texte)
        f_espagnol = pool.submit(lecon, "espagnol", NIVEAU_ESPAGNOL, titres, date_texte)
        f_quiz = pool.submit(donnees_quiz, titres, date_texte)

        c = {
            "numero": numero, "date_texte": date_texte,
            "meteo": f_meteo.result(), "priere": f_priere.result(),
            "verset": f_verset.result(), "une": f_une.result(),
        }
        actu = {nom: f.result() for nom, f in f_actu.items()}
        dossier, anglais, espagnol = f_dossier.result(), f_anglais.result(), f_espagnol.result()
        arabe, echecs, quiz = f_arabe.result(), f_echecs.result(), f_quiz.result()
        citations, ce_jour = f_citations.result(), f_ce_jour.result()

    # Pages dans l'ordre du journal (une rubrique sans contenu est simplement omise)
    pages = [(nom, page_actu(nom, actu[nom])) for nom in ("Monde", "Algérie")]
    if dossier:
        pages.append(("Le dossier du jour", page_dossier(dossier)))
    for nom in ("Économie", "Tech & IA", "Sciences", "Culture", "Sport"):
        pages.append((nom, page_actu(nom, actu[nom])))
    if anglais:
        pages.append(("English corner", page_lecon("English corner", NIVEAU_ANGLAIS, anglais)))
    if espagnol:
        pages.append(("Rincón español",
                      page_lecon("Rincón español", NIVEAU_ESPAGNOL, espagnol)))
    if arabe:
        pages.append(("Arabe & darija", page_arabe(arabe)))
    if echecs or quiz:
        pages.append(("Jeux de l'esprit", page_jeux(echecs, quiz)))
    if citations:
        pages.append(("Citations & lectures", page_citations(citations)))
    if ce_jour:
        pages.append(("Ce jour-là",
                      page_ce_jour(ce_jour, f"{jour.day} {MOIS[jour.month - 1]}")))
    if echecs or quiz:
        pages.append(("Solutions", page_solutions(echecs, quiz)))
    c["sommaire"] = [titre for titre, _ in pages]

    livre = epub.EpubBook()
    livre.set_identifier(str(uuid.uuid4()))
    livre.set_title(f"{TITRE[0]} {TITRE[1]} n° {numero} — {date_texte}")
    livre.set_language("fr")
    livre.add_author(f"{TITRE[0]} {TITRE[1]}")
    livre.add_item(epub.EpubItem(uid="style", file_name="style.css",
                                 media_type="text/css", content=CSS))
    if echecs:
        livre.add_item(epub.EpubItem(uid="echecs", file_name="echecs.svg",
                                     media_type="image/svg+xml",
                                     content=echecs["svg"].encode("utf-8")))

    chapitres = [chapitre("une.xhtml", "La une", page_une(c))]
    for i, (titre, corps) in enumerate(pages, 1):
        chapitres.append(chapitre(f"page{i:02d}.xhtml", titre, corps))
    for ch in chapitres:
        livre.add_item(ch)
    livre.toc = chapitres
    livre.spine = chapitres + ["nav"]
    livre.add_item(epub.EpubNcx())
    livre.add_item(epub.EpubNav())

    SORTIE.mkdir(exist_ok=True)
    epub.write_epub(str(SORTIE / "journal.epub"), livre)
    (SORTIE / "index.html").write_text(
        f"<!doctype html><meta charset='utf-8'><title>{e(TITRE[0])} {e(TITRE[1])}</title>"
        f"<p><a href='journal.epub'>{e(TITRE[0])} {e(TITRE[1])} n° {numero} — "
        f"{e(date_texte)}</a></p>",
        encoding="utf-8",
    )
    log(f"✓ {SORTIE / 'journal.epub'} ({len(chapitres)} pages)")


if __name__ == "__main__":
    main()
