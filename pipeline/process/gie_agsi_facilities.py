"""GIE AGSI+ facility listing -> supply/gas_storage_sites.

Input : data/raw/gie_agsi_facilities/agsi_facilities.json (operators and their facilities; no locations)
Output: supply/gas_storage_sites   (one row per storage site in Germany, France, Italy and Austria, with the
                                    number of operators reporting it and an approximate location)

AGSI+ names facilities, often as pools of several sites ("VGS SALINE (Tersanne, Etrez, Manosque)"), and gives
no coordinates. Site names found in the facility names are placed at the nearby town from SITES below, by hand
(about 10-20 km accuracy). Pools that name no site are listed in the notes.
"""
import json
import re
import unicodedata
from datetime import date

import pandas as pd

from ..common import RAW_DIR, read_manifest, write_tidy

SOURCE_ID = "gie_agsi_facilities"
FILE = "agsi_facilities.json"
COUNTRIES = {"DE": "Germany", "FR": "France", "IT": "Italy", "AT": "Austria"}
KINDS = {"DSR": "depleted field", "ASR": "aquifer", "ASF": "salt cavern", "SRC": "rock cavern"}

# site: (pattern in the accent-free, lower-case facility name, country, lat, lon)
SITES = {
    # Germany
    "Rehden": (r"rehden", "DE", 52.6, 8.5),
    "Jemgum": (r"jemgum", "DE", 53.3, 7.4),
    "Nüttermoor": (r"nuttermoor", "DE", 53.2, 7.4),
    "Etzel": (r"etzel", "DE", 53.5, 7.8),
    "Epe": (r"\bepe\b", "DE", 52.2, 7.0),
    "Uelsen": (r"uelsen", "DE", 52.5, 6.9),
    "Harsefeld": (r"harsefeld", "DE", 53.5, 9.5),
    "Lesum": (r"lesum", "DE", 53.2, 8.7),
    "Kiel-Rönne": (r"kiel", "DE", 54.3, 10.1),
    "Kraak": (r"kraak", "DE", 53.5, 11.3),
    "Ronnenberg-Empelde": (r"empelde", "DE", 52.3, 9.7),
    "Peckensen": (r"peckensen", "DE", 52.8, 11.1),
    "Rüdersdorf": (r"rudersdorf", "DE", 52.5, 13.8),
    "Staßfurt": (r"stassfurt", "DE", 51.9, 11.6),
    "Bernburg": (r"bernburg", "DE", 51.8, 11.7),
    "Katharina": (r"katharina", "DE", 51.7, 11.9),
    "Bad Lauchstädt": (r"bad lauchstadt", "DE", 51.4, 11.9),
    "Allmenhausen": (r"allmenhausen", "DE", 51.3, 10.7),
    "Kirchheiligen": (r"kirchheiligen", "DE", 51.2, 10.6),
    "Reckrod": (r"reckrod", "DE", 50.8, 9.8),
    "Hähnlein": (r"haehnlein|hahnlein", "DE", 49.7, 8.6),
    "Stockstadt": (r"stockstadt", "DE", 49.8, 8.5),
    "Frankenthal": (r"frankenthal", "DE", 49.5, 8.4),
    "Wolfersberg": (r"wolfersberg", "DE", 48.1, 11.9),
    "Bierwang": (r"bierwang", "DE", 48.1, 12.2),
    "Schmidhausen": (r"schmidhausen", "DE", 47.9, 12.0),
    "Inzenham-West": (r"inzenham", "DE", 47.8, 12.1),
    "Breitbrunn": (r"breitbrunn", "DE", 47.9, 12.4),
    # France
    "Saint-Clair-sur-Epte": (r"saint-clair-sur-epte", "FR", 49.2, 1.7),
    "Saint-Illiers": (r"saint-illiers", "FR", 49.0, 1.5),
    "Beynes": (r"beynes", "FR", 48.9, 1.9),
    "Gournay-sur-Aronde": (r"gournay-sur-aronde", "FR", 49.5, 2.7),
    "Germigny-sous-Coulombs": (r"germi\w*-sous-coulombs", "FR", 49.1, 3.2),
    "Trois-Fontaines-l'Abbaye": (r"trois fontaines", "FR", 48.7, 5.0),
    "Cerville": (r"cerville", "FR", 48.7, 6.3),
    "Chémery": (r"chemery", "FR", 47.35, 1.45),
    "Soings-en-Sologne": (r"soings-en-sologne", "FR", 47.45, 1.55),
    "Céré-la-Ronde": (r"cere-la-ronde", "FR", 47.3, 1.2),
    "Étrez": (r"etrez", "FR", 46.3, 5.2),
    "Tersanne": (r"tersanne", "FR", 45.2, 5.0),
    "Manosque": (r"manosque", "FR", 43.8, 5.8),
    "Lussagnet": (r"lussagnet", "FR", 43.8, -0.2),
    # Italy
    "Collalto": (r"collalto", "IT", 45.9, 12.2),
    "Brugherio": (r"brugherio", "IT", 45.6, 9.3),
    "Settala": (r"settala", "IT", 45.5, 9.4),
    "Sergnano": (r"sergnano", "IT", 45.4, 9.7),
    "Ripalta": (r"ripalta", "IT", 45.3, 9.7),
    "Cornegliano": (r"cornegliano", "IT", 45.3, 9.5),
    "Bordolano": (r"bordolano", "IT", 45.3, 10.0),
    "Cortemaggiore": (r"cortemaggiore", "IT", 45.0, 9.9),
    "Sabbioncello": (r"sabbioncello", "IT", 44.9, 11.8),
    "Minerbio": (r"minerbio", "IT", 44.6, 11.5),
    "San Potito and Cotignola": (r"san potito|cotignola", "IT", 44.4, 11.9),
    "Cellino": (r"cellino", "IT", 42.6, 14.0),
    "Fiume Treste": (r"fiume treste", "IT", 42.1, 14.6),
    # Austria
    "Haidach": (r"haidach", "AT", 48.0, 13.2),
    "7Fields": (r"7 ?fields", "AT", 48.1, 13.1),
    "Puchkirchen / Haag": (r"puchkirchen", "AT", 48.0, 13.6),
    "Aigelsbrunn": (r"aigelsbrunn", "AT", 48.2, 13.6),
    "Schönkirchen-Reyersdorf": (r"schonkirchen", "AT", 48.4, 16.6),
    "Tallesbrunn": (r"tallesbrunn", "AT", 48.4, 16.8),
}


def plain(text: str) -> str:
    """Lower case without accents, so 'Chéméry' matches 'chemery'."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    today = date.today().isoformat()
    found = {site: {"operators": set(), "types": []} for site in SITES}
    unplaced = []
    for company in json.loads(path.read_text(encoding="utf-8")):
        operator = re.sub(r"\s*\(\d+\)$", "", company["short_name"]).strip()  # drop AGSI+ footnote numbers
        for f in company["facilities"]:
            # current facilities only: historical entries carry an end date in the past
            if f["country"] not in COUNTRIES or (f["operational_end_date"] or "9999") < today:
                continue
            sites = [s for s, (pattern, country, *_) in SITES.items()
                     if country == f["country"] and re.search(pattern, plain(f["name"]))]
            if not sites:
                unplaced.append(f"{f['name']} ({operator})")
            for s in sites:
                found[s]["operators"].add(operator)
                found[s]["types"].append(f["type"])

    rows = []
    for site, (_, country, lat, lon) in SITES.items():
        operators, types = found[site]["operators"], [t for t in found[site]["types"] if t in KINDS]
        if not operators:
            print(f"  warning: {site} is no longer named in the AGSI+ listing")
            continue
        rows.append({
            "year": int(read_manifest(path.parent)[FILE]["retrieved"][:4]),
            "category": site,
            "value": len(operators),
            "unit": "operators",
            "lat": lat,
            "lon": lon,
            "country": COUNTRIES[country],
            # pools of mixed sites (GRP) give no type per site
            "kind": KINDS[max(set(types), key=types.count)] if types else "not given",
            "detail": ", ".join(sorted(operators)),
        })
    notes = f"{len(rows)} sites. Current AGSI+ entries that name no site: {'; '.join(unplaced)}." if unplaced else f"{len(rows)} sites."
    write_tidy(pd.DataFrame(rows), "supply/gas_storage_sites", [path], __name__, notes=notes)
