"""Shared paths, constants and helpers for the embassies project.

Raw inputs (read in place, never modified):
  /home/claude/work/embassies/raw/osm_diplomatic.json
      17,573 OpenStreetMap features tagged office=diplomatic or amenity=embassy, fetched in 2026 through the Overpass API
      (OpenStreetMap contributors, ODbL 1.0). One object per feature: id (n/w/r + OSM id), lat, lon (ways and relations:
      their centre) and the tags name, name:en, office, diplomatic, embassy, consulate, country (the SENDING state,
      ISO 3166-1 alpha-2 by convention), target (the receiving state or organisation), addr:city, addr:country,
      wikidata, website, operator, start_date, amenity.
  /home/claude/work/embassies/raw/wd_missions.tsv
      Wikidata items (CC0) fetched in 2026 by instance-of class: qid, label, type (the class QID), op (P137 operator,
      the sending state) and op_label, host (P17 country) and host_label, coord (P625), inception (P571), dissolved
      (P576). Classes requested: Q3917681 (embassy), Q7843791 (consulate), Q5244910 (representative office),
      Q2385804, Q2001305, Q1137299. Checked by label in code/02_gazetteer.py: Q2385804 holds schools and colleges
      (educational institution) and Q2001305 television channels, so both are dropped; Q1137299 returned no items.
  /home/claude/work/embassies/raw/cow_diplomatic_exchange_2006v1.csv
      Correlates of War Diplomatic Exchange data set v2006.1 (Bayer 2006): directed state dyads ccode1, ccode2, year
      (1817 to 2005, about every five years), DR_at_1 (level of representation of state 2 in state 1: 0 none,
      1 charge d'affaires, 2 minister, 3 ambassador, 9 other), DR_at_2, DE. Free to use with citation.
  /home/claude/work/embassies/ext/states2011.csv
      Correlates of War State System Membership list v2011 (ccode, stateabb, statenme, start and end dates), from a
      GitHub copy (raw.githubusercontent.com/burakbayramli/books/master/The_War_Trap/states2011.csv); used only to name
      COW country codes. Mapping to ISO codes and capitals is in code/03_cow.py.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_50m_admin_0_countries.geojson,
  ne_10m_populated_places_simple.geojson, ne_50m_land.geojson
      Natural Earth (public domain): borders used to place each mission in a host territory, outlines for the maps,
      and populated places used to name the city of each mission.
External comparison figures (quoted, not redistributed): Lowy Institute Global Diplomacy Index 2024, key findings page
(globaldiplomacyindex.lowyinstitute.org/key_findings): total posts for China 274, United States 271, Turkiye 252,
Japan 251, Indonesia 130, Australia 124, Taiwan 110 (14 of them officially accredited).
"""
import json, gzip, os, re, unicodedata
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("EMB_RAW", "/home/claude/work/embassies/raw")
EXT = os.environ.get("EMB_EXT", "/home/claude/work/embassies/ext")
OSM = os.path.join(RAW, "osm_diplomatic.json")
WD = os.path.join(RAW, "wd_missions.tsv")
COW = os.path.join(RAW, "cow_diplomatic_exchange_2006v1.csv")
COW_STATES = os.path.join(EXT, "states2011.csv")
GEO = os.environ.get("EMB_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("EMB_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("EMBTMP", "/dev/shm/embassies"), "work")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "embassies"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23899269"                   # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/embassies/"             # filled in by the publisher
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# Lowy Institute Global Diplomacy Index 2024 (key findings page): total diplomatic posts. Lowy counts embassies,
# high commissions, consulates-general, consulates, permanent missions and representative offices, not honorary posts.
LOWY = {"CN": 274, "US": 271, "TR": 252, "JP": 251, "ID": 130, "AU": 124, "TW": 110}

# Mission types, in order of rank. 'group' is what is compared and counted.
TYPES = {
    "embassy":           ("Embassy", "resident"),
    "high_commission":   ("High commission", "resident"),
    "nunciature":        ("Apostolic nunciature", "resident"),
    "delegation":        ("Delegation (EU and others)", "resident"),
    "interests_section": ("Interests section", "resident"),
    "perm_mission":      ("Permanent mission to an organisation", "multilateral"),
    "consulate_general": ("Consulate-general", "consular"),
    "consulate":         ("Consulate or consular office", "consular"),
    "honorary":          ("Honorary consulate", "honorary"),
    "liaison":           ("Representative or liaison office", "liaison"),
    "embassy_office":    ("Embassy section or office (trade, culture, consular)", "office"),
}
TYPE_ORDER = list(TYPES)
TCOL = {  # map colours by type (light paper)
    "embassy": "#B3261E", "high_commission": "#7A2E8E", "nunciature": "#C98A00", "delegation": "#1F5FAD",
    "interests_section": "#6B6B6B", "perm_mission": "#0E7C7B", "consulate_general": "#E07B39", "consulate": "#E9A66B",
    "honorary": "#9AA7B5", "liaison": "#2E8B57", "embassy_office": "#B8A27A"}

UN193 = """AF AL DZ AD AO AG AR AM AU AT AZ BS BH BD BB BY BE BZ BJ BT BO BA BW BR BN BG BF BI CV KH CM CA CF TD CL CN CO KM
CG CD CR CI HR CU CY CZ DK DJ DM DO EC EG SV GQ ER EE SZ ET FJ FI FR GA GM GE DE GH GR GD GT GN GW GY HT HN HU IS IN ID IR
IQ IE IL IT JM JP JO KZ KE KI KP KR KW KG LA LV LB LS LR LY LI LT LU MG MW MY MV ML MT MH MR MU MX FM MD MC MN ME MA MZ MM
NA NR NP NL NZ NI NE NG MK NO OM PK PW PA PG PY PE PH PL PT QA RO RU RW KN LC VC WS SM ST SA SN RS SC SL SG SK SI SB SO ZA
SS ES LK SD SR SE CH SY TJ TZ TH TL TG TO TT TN TR TM TV UG UA AE GB US UY UZ VU VE VN YE ZM ZW""".split()
assert len(UN193) == 193 and len(set(UN193)) == 193
# Other entities that send or receive missions in the data, described as the data record them.
OTHER_STATES = {"VA": "Holy See", "PS": "Palestine", "TW": "Taiwan", "XK": "Kosovo", "EH": "Sahrawi Arab Democratic Republic"}
NONSTATE = {"EU": "European Union", "XO": "Sovereign Order of Malta"}
STATES = UN193 + list(OTHER_STATES)
NAME_FIX = {"CN": "China", "US": "United States", "GB": "United Kingdom", "RU": "Russia", "KR": "South Korea",
            "KP": "North Korea", "CD": "DR Congo", "CG": "Republic of the Congo", "CZ": "Czechia", "TR": "Turkiye",
            "CI": "Cote d'Ivoire", "CV": "Cabo Verde", "SZ": "Eswatini", "TL": "Timor-Leste", "FM": "Micronesia",
            "BS": "Bahamas", "GM": "Gambia", "VA": "Holy See", "PS": "Palestine", "TW": "Taiwan", "XK": "Kosovo",
            "EH": "Sahrawi Arab Democratic Republic", "MK": "North Macedonia", "LA": "Laos", "SY": "Syria", "IR": "Iran",
            "VN": "Vietnam", "BN": "Brunei", "MD": "Moldova", "TZ": "Tanzania", "BO": "Bolivia", "VE": "Venezuela",
            "ST": "Sao Tome and Principe", "KN": "Saint Kitts and Nevis", "VC": "Saint Vincent and the Grenadines",
            "LC": "Saint Lucia", "EU": "European Union", "XO": "Sovereign Order of Malta"}
TERRITORY_NAME = {"EH": "Western Sahara", "VA": "Vatican City"}

# International organisations a permanent mission may be accredited to (code -> name, seat city)
ORGS = {"UN": ("United Nations", "New York and Geneva"), "EU": ("European Union", "Brussels"), "COE": ("Council of Europe", "Strasbourg"),
        "OECD": ("OECD", "Paris"), "UNESCO": ("UNESCO", "Paris"), "NATO": ("NATO", "Brussels"), "OSCE": ("OSCE", "Vienna"),
        "WTO": ("World Trade Organization", "Geneva"), "FAO": ("FAO", "Rome"), "AU_ORG": ("African Union", "Addis Ababa"),
        "ASEAN": ("ASEAN", "Jakarta"), "OAS": ("Organization of American States", "Washington"), "IAEA": ("IAEA and UN Vienna", "Vienna"),
        "INTL": ("an international organisation", "")}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr":
        y = int(v); return f"{-y} BC" if y < 0 else (f"AD {y}" if y < 1000 else str(y))
    if f == "ord":
        n = int(v); suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suf}"
    raise ValueError(f)


def gc_km(lat1, lon1, lat2, lon2):
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))
