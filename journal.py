"""Mon Journal du Matin — génère un EPUB quotidien (actualités, météo, prière, langues).

Mise en page inspirée de Signal Matin (github.com/sosoj92/signal-matin, licence MIT).
"""

import datetime as dt
import html
import json
import os
import re
import sys
import uuid
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
import requests
from ebooklib import epub

# ─────────────────────────────── Personnalisation ───────────────────────────────

TITRE = "Sina"                 # partie grasse du nom
DEVISE = "Journal"             # partie italique du nom
EDITION = "Édition du matin"

VILLE = {
    "nom": "Alger",
    "latitude": 36.7538,
    "longitude": 3.0588,
    "fuseau": "Africa/Algiers",
}

# Méthode de calcul Aladhan : 19 = Algérie ; 12 = UOIF France ; 3 = Ligue islamique mondiale
METHODE_PRIERE = 19

NIVEAU_ANGLAIS = "B1"
NIVEAU_ESPAGNOL = "A2"

ARTICLES_PAR_RUBRIQUE = 5

# Flux RSS par rubrique : une source en panne n'empêche pas le reste.
SOURCES = {
    "Algérie": [
        "https://www.tsa-algerie.com/feed/",
        "https://www.algerie360.com/feed/",
    ],
    "International": [
        "https://www.france24.com/fr/rss",
        "https://www.lemonde.fr/international/rss_full.xml",
    ],
    "Économie": [
        "https://www.lemonde.fr/economie/rss_full.xml",
    ],
    "Sciences & Tech": [
        "https://www.numerama.com/feed/",
        "https://www.futura-sciences.com/rss/actualites.xml",
    ],
    "Culture": [
        "https://www.lemonde.fr/culture/rss_full.xml",
    ],
    "Sport": [
        "https://www.dzfoot.com/feed",
        "https://www.lequipe.fr/rss/actu_rss.xml",
    ],
}

MODELE = "claude-opus-5-5"

# ────────────────────────────────────────────────────────────────────────────────

SORTIE = Path("public")
HTTP = {"User-Agent": "Mozilla/5.0 (MonJournalDuMatin)"}

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


def log(msg):
    print(msg, file=sys.stderr)


def nettoyer(texte, limite=600):
    texte = html.unescape(re.sub(r"<[^>]+>", " ", texte or ""))
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte if len(texte) <= limite else texte[:limite].rsplit(" ", 1)[0] + "…"


def e(texte):
    return html.escape(texte or "", quote=True)


# ─────────────────────────────── Collecte ───────────────────────────────

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


def collecter_actus(maintenant):
    limite = maintenant - dt.timedelta(hours=36)
    rubriques = {}
    for rubrique, urls in SOURCES.items():
        vus, articles = set(), []
        for url in urls:
            for a in lire_flux(url):
                cle = a["titre"].lower()
                if not a["titre"] or cle in vus or (a["date"] and a["date"] < limite):
                    continue
                vus.add(cle)
                articles.append(a)
        articles.sort(key=lambda a: a["date"] or limite, reverse=True)
        rubriques[rubrique] = articles[:ARTICLES_PAR_RUBRIQUE]
    return rubriques


def meteo():
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=20, params={
            "latitude": VILLE["latitude"], "longitude": VILLE["longitude"],
            "timezone": VILLE["fuseau"], "forecast_days": 1,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,"
                     "precipitation_probability_max,windspeed_10m_max",
        })
        r.raise_for_status()
        j = r.json()["daily"]
        return {
            "ciel": METEO_CODES.get(j["weathercode"][0], "—"),
            "min": round(j["temperature_2m_min"][0]),
            "max": round(j["temperature_2m_max"][0]),
            "pluie": j["precipitation_probability_max"][0],
            "vent": round(j["windspeed_10m_max"][0]),
        }
    except Exception as err:
        log(f"Météo indisponible : {err}")
        return None


def priere(jour):
    try:
        r = requests.get(
            f"https://api.aladhan.com/v1/timings/{jour:%d-%m-%Y}", timeout=20,
            params={"latitude": VILLE["latitude"], "longitude": VILLE["longitude"],
                    "method": METHODE_PRIERE},
        )
        r.raise_for_status()
        data = r.json()["data"]
        hijri = data["date"]["hijri"]
        return {
            "horaires": [(nom, data["timings"][cle][:5]) for cle, nom in PRIERES],
            "hegire": f"{int(hijri['day'])} {MOIS_HEGIRE[hijri['month']['number'] - 1]} "
                      f"{hijri['year']}",
        }
    except Exception as err:
        log(f"Horaires de prière indisponibles : {err}")
        return None


# ─────────────────────────────── Claude ───────────────────────────────

SCHEMA_LECON = {
    "type": "object",
    "properties": {
        "theme": {"type": "string"},
        "vocabulaire": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"mot": {"type": "string"}, "traduction": {"type": "string"},
                               "exemple": {"type": "string"}},
                "required": ["mot", "traduction", "exemple"],
                "additionalProperties": False,
            },
        },
        "expression": {"type": "string"},
        "explication": {"type": "string"},
        "texte": {"type": "string"},
        "traduction_texte": {"type": "string"},
    },
    "required": ["theme", "vocabulaire", "expression", "explication", "texte",
                 "traduction_texte"],
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "essentiel": {"type": "array", "items": {"type": "string"}},
        "rubriques": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nom": {"type": "string"},
                    "resumes": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["nom", "resumes"],
                "additionalProperties": False,
            },
        },
        "anglais": SCHEMA_LECON,
        "espagnol": SCHEMA_LECON,
    },
    "required": ["essentiel", "rubriques", "anglais", "espagnol"],
    "additionalProperties": False,
}


def enrichir(rubriques, date_texte):
    """Résumés et leçons de langue. Retourne None sans clé API ou en cas d'échec."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log("Pas de clé ANTHROPIC_API_KEY : journal sans résumés ni leçons.")
        return None

    import anthropic

    corpus = []
    for nom, articles in rubriques.items():
        corpus.append(f"## {nom}")
        for i, a in enumerate(articles, 1):
            corpus.append(f"{i}. {a['titre']} ({a['source']})\n   {a['resume']}")
    consigne = f"""Nous sommes le {date_texte}. Voici les dépêches du matin, par rubrique.

{chr(10).join(corpus)}

Produis, en français :
- "essentiel" : 3 à 5 phrases qui résument les faits les plus importants du jour.
- "rubriques" : pour chaque rubrique ci-dessus, dans le même ordre et avec le même nom,
  un résumé de 2 ou 3 phrases par article, dans l'ordre des articles. Reste factuel et
  n'invente rien qui ne figure pas dans la dépêche.
- "anglais" : une leçon d'anglais niveau {NIVEAU_ANGLAIS} inspirée d'une actualité du jour :
  un thème, 5 mots de vocabulaire (mot anglais, traduction française, phrase d'exemple en
  anglais), une expression idiomatique et son explication en français, un court texte
  de 60 à 90 mots en anglais et sa traduction française.
- "espagnol" : la même chose en espagnol, niveau {NIVEAU_ESPAGNOL}, sur un autre thème."""

    client = anthropic.Anthropic()
    try:
        reponse = client.beta.messages.create(
            model=MODELE,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            extra_body={"fallbacks": "default"},
            output_config={"effort": "low",
                           "format": {"type": "json_schema", "schema": SCHEMA}},
            system="Tu es le rédacteur en chef d'un quotidien francophone sobre et précis.",
            messages=[{"role": "user", "content": consigne}],
        )
    except anthropic.APIConnectionError as err:
        log(f"Claude injoignable : {err}")
        return None
    except anthropic.APIStatusError as err:
        log(f"Erreur de l'API Claude ({err.status_code}) : {err.message}")
        return None

    if reponse.stop_reason in ("refusal", "max_tokens"):
        log(f"Réponse de Claude inutilisable (stop_reason={reponse.stop_reason}).")
        return None
    texte = next((b.text for b in reponse.content if b.type == "text"), "")
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        log("Réponse de Claude illisible.")
        return None


# ─────────────────────────────── Mise en page ───────────────────────────────

CSS = """
body { font-family: Georgia, "Times New Roman", serif; line-height: 1.5; margin: 0 4%; }
.titre { text-align: center; border-bottom: 3px double #111; padding-bottom: .4em;
         margin-bottom: .6em; }
.titre h1 { font-size: 2.6em; margin: .2em 0 0; letter-spacing: .02em; }
.titre h1 b { font-weight: 900; }
.titre h1 i { font-weight: 400; }
.titre .bandeau { font-size: .8em; text-transform: uppercase; letter-spacing: .12em;
                  border-top: 1px solid #111; margin-top: .5em; padding-top: .3em; }
h2 { font-size: 1.05em; text-transform: uppercase; letter-spacing: .1em;
     border-bottom: 1px solid #111; padding-bottom: .15em; margin-top: 1.6em; }
h3 { font-size: 1.1em; margin: 1em 0 .2em; }
.source { font-size: .75em; color: #666; text-transform: uppercase; letter-spacing: .06em; }
.encadre { border: 1px solid #111; padding: .6em .9em; margin: 1em 0; }
table { width: 100%; border-collapse: collapse; }
td { padding: .15em .3em; border-bottom: 1px dotted #999; }
td.h { text-align: right; font-variant-numeric: tabular-nums; }
ul.essentiel li { margin-bottom: .4em; }
.vo { font-style: italic; }
.note { font-size: .75em; color: #666; }
a { color: inherit; }
"""


def page_une(date_texte, pri, met, ia):
    blocs = [f"""<div class="titre">
<h1><b>{e(TITRE)}</b> <i>{e(DEVISE)}</i></h1>
<div class="bandeau">{e(EDITION)} — {e(date_texte)}{
    f" — {e(pri['hegire'])}" if pri else ""}</div>
</div>"""]
    if ia and ia.get("essentiel"):
        items = "".join(f"<li>{e(p)}</li>" for p in ia["essentiel"])
        blocs.append(f"<h2>L'essentiel</h2><ul class='essentiel'>{items}</ul>")
    if met:
        blocs.append(f"""<div class="encadre"><b>Météo à {e(VILLE['nom'])}</b> —
{e(met['ciel'])}, {met['min']}° / {met['max']}°. Pluie : {met['pluie']} %.
Vent : {met['vent']} km/h.</div>""")
    if pri:
        lignes = "".join(f"<tr><td>{e(n)}</td><td class='h'>{h}</td></tr>"
                         for n, h in pri["horaires"])
        blocs.append(f"""<div class="encadre"><b>Horaires de prière — {e(VILLE['nom'])}</b>
<table>{lignes}</table>
<p class="note">Date hégirienne calculée : elle peut différer d'un jour de l'annonce
officielle.</p></div>""")
    return "\n".join(blocs)


def page_rubrique(nom, articles, resumes):
    blocs = [f"<h2>{e(nom)}</h2>"]
    if not articles:
        blocs.append("<p class='note'>Aucune dépêche disponible ce matin.</p>")
    for i, a in enumerate(articles):
        resume = resumes[i] if i < len(resumes) else a["resume"]
        blocs.append(f"""<h3>{e(a['titre'])}</h3>
<p class="source">{e(a['source'])}</p>
<p>{e(resume)}</p>
{f'<p class="note"><a href="{e(a["lien"])}">Lire l’article</a></p>' if a['lien'] else ''}""")
    return "\n".join(blocs)


def page_lecon(titre, lecon):
    vocab = "".join(
        f"<tr><td><b>{e(v['mot'])}</b></td><td>{e(v['traduction'])}</td></tr>"
        f"<tr><td colspan='2' class='vo'>{e(v['exemple'])}</td></tr>"
        for v in lecon["vocabulaire"]
    )
    return f"""<h2>{e(titre)}</h2>
<h3>{e(lecon['theme'])}</h3>
<table>{vocab}</table>
<div class="encadre"><b class="vo">{e(lecon['expression'])}</b><br/>{e(lecon['explication'])}</div>
<p class="vo">{e(lecon['texte'])}</p>
<p>{e(lecon['traduction_texte'])}</p>"""


def chapitre(nom_fichier, titre, corps):
    c = epub.EpubHtml(title=titre, file_name=nom_fichier, lang="fr")
    c.content = f"<html><body>{corps}</body></html>"
    c.add_link(href="style.css", rel="stylesheet", type="text/css")
    return c


def construire_epub(jour, date_texte, rubriques, pri, met, ia):
    livre = epub.EpubBook()
    livre.set_identifier(str(uuid.uuid4()))
    livre.set_title(f"{TITRE} {DEVISE} — {date_texte}")
    livre.set_language("fr")
    livre.add_author(f"{TITRE} {DEVISE}")
    style = epub.EpubItem(uid="style", file_name="style.css", media_type="text/css",
                          content=CSS)
    livre.add_item(style)

    chapitres = [chapitre("une.xhtml", "À la une", page_une(date_texte, pri, met, ia))]
    resumes_ia = {r["nom"]: r["resumes"] for r in (ia or {}).get("rubriques", [])}
    for i, (nom, articles) in enumerate(rubriques.items(), 1):
        chapitres.append(chapitre(f"rubrique{i}.xhtml", nom,
                                  page_rubrique(nom, articles, resumes_ia.get(nom, []))))
    if ia:
        chapitres.append(chapitre("anglais.xhtml", "English corner",
                                  page_lecon(f"English corner — {NIVEAU_ANGLAIS}", ia["anglais"])))
        chapitres.append(chapitre("espagnol.xhtml", "Rincón español",
                                  page_lecon(f"Rincón español — {NIVEAU_ESPAGNOL}", ia["espagnol"])))

    for c in chapitres:
        livre.add_item(c)
    livre.toc = chapitres
    livre.spine = ["nav"] + chapitres
    livre.add_item(epub.EpubNcx())
    livre.add_item(epub.EpubNav())

    SORTIE.mkdir(exist_ok=True)
    epub.write_epub(str(SORTIE / "journal.epub"), livre)
    (SORTIE / "index.html").write_text(
        f"<!doctype html><meta charset='utf-8'><title>{e(TITRE)} {e(DEVISE)}</title>"
        f"<p><a href='journal.epub'>{e(TITRE)} {e(DEVISE)} — {e(date_texte)}</a></p>",
        encoding="utf-8",
    )


def main():
    maintenant = dt.datetime.now(ZoneInfo(VILLE["fuseau"]))
    jour = maintenant.date()
    date_texte = f"{JOURS[jour.weekday()]} {jour.day} {MOIS[jour.month - 1]} {jour.year}"
    log(f"Journal du {date_texte}")

    rubriques = collecter_actus(maintenant.astimezone(dt.timezone.utc))
    met = meteo()
    pri = priere(jour)
    ia = enrichir(rubriques, date_texte)
    construire_epub(jour, date_texte, rubriques, pri, met, ia)
    log(f"✓ {SORTIE / 'journal.epub'}")


if __name__ == "__main__":
    main()
