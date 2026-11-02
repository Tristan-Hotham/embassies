"""The universe of states and territories, names for matching, capitals, and the host lookup.

States: the 193 UN member states plus the Holy See, Palestine, Taiwan, Kosovo and the Sahrawi Arab Democratic Republic
(SADR), the entities that appear as senders of missions in the data. Non-state senders kept separately: the European
Union and the Sovereign Order of Malta. Territories: every Natural Earth 10m admin-0 unit, each assigned to the state
it is counted under (dependencies under their sovereign; Natural Earth's Somaliland and Northern Cyprus units under
Somalia and Cyprus, as the states recognised by the UN; Palestine, Taiwan, Kosovo and Western Sahara as their own units,
as Natural Earth draws them). Output: WORK/countries.pkl and data/countries.csv."""
import pickle
import pandas as pd
from shapely.geometry import shape
from shapely.strtree import STRtree
from common import *

NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
SOV_STATE = {"GB1": "GB", "CH1": "CN", "US1": "US", "FR1": "FR", "NL1": "NL", "DN1": "DK", "AU1": "AU", "NZ1": "NZ",
             "FI1": "FI", "KA1": "KZ", "CU1": "CU", "SOL": "SO", "CYN": "CY", "CNM": "CY", "IS1": "IL"}
UNIT_FIX = {"PSX": "PS", "SAH": "EH", "KOS": "XK", "TWN": "TW", "VAT": "VA", "ESB": "GB", "WSB": "GB", "USG": "US",
            "BRI": "BR", "KAB": "KZ", "SPI": "AR"}

units = []
for f in NE:
    p = f["properties"]
    iso = p["ISO_A2_EH"] if p["ISO_A2_EH"] != "-99" else None
    a3 = p["ADM0_A3"]
    if a3 in UNIT_FIX:
        state = UNIT_FIX[a3]
    elif iso in STATES and p["TYPE"] in ("Sovereign country", "Country", "Sovereignty", "Disputed") and a3 not in ("FLK", "GIB", "IOT"):
        state = iso
    else:
        state = SOV_STATE.get(p["SOV_A3"]) or (p["SOV_A3"][:2] if p["SOV_A3"][:2] in STATES else None)
    units.append({"a3": a3, "iso": iso, "unit": p["NAME_EN"], "state": state, "type": p["TYPE"], "geom": shape(f["geometry"]),
                  "pop": p["POP_EST"], "continent": p["CONTINENT"], "subregion": p["SUBREGION"], "wd": p["WIKIDATAID"],
                  "names": {p[k] for k in ("NAME", "NAME_LONG", "ADMIN", "FORMAL_EN", "NAME_EN", "NAME_SORT", "GEOUNIT", "BRK_NAME") if p.get(k)},
                  "intl": {p[k] for k in ("NAME_DE", "NAME_FR", "NAME_ES", "NAME_IT", "NAME_PT", "NAME_NL", "NAME_PL", "NAME_SV",
                                          "NAME_TR", "NAME_HU", "NAME_ID", "NAME_VI", "NAME_RU", "NAME_UK", "NAME_EL", "NAME_AR",
                                          "NAME_FA", "NAME_ZH", "NAME_ZHT", "NAME_JA", "NAME_KO", "NAME_HE") if p.get(k)}})
miss = [u["unit"] for u in units if u["state"] is None]
print("units without a state:", miss)

# ---------------- states ----------------
S = {}
for code in STATES:
    us = [u for u in units if u["state"] == code]
    home = [u for u in us if u["iso"] == code or (code in OTHER_STATES and u["a3"] in UNIT_FIX and UNIT_FIX[u["a3"]] == code)]
    assert home, code
    h = max(home, key=lambda u: u["geom"].area)
    S[code] = {"code": code, "name": NAME_FIX.get(code, h["unit"]), "pop": int(sum(u["pop"] for u in home)),
               "area_deg": sum(u["geom"].area for u in home), "continent": h["continent"], "subregion": h["subregion"],
               "wd": h["wd"], "un": code in UN193, "names": set().union(*[u["names"] for u in home]),
               "intl": set().union(*[u["intl"] for u in home])}
# areas in km2 (equal-area projection)
import pyproj
import warnings; warnings.filterwarnings('ignore')
from shapely.ops import transform, unary_union
eq = pyproj.Transformer.from_crs("EPSG:4326", "ESRI:54034", always_xy=True).transform
for code in STATES:
    g = unary_union([u["geom"] for u in units if u["state"] == code and (u["iso"] == code or u["a3"] in UNIT_FIX)])
    a = transform(eq, g).area / 1e6
    S[code]["area_km2"] = round(a, 2) if a < 10 else round(a)

# English demonyms and common alternative names (for names such as "British Embassy" or "Embassy of Turkey")
ALT = {
 "AF": "Afghan", "AL": "Albanian", "DZ": "Algerian", "AD": "Andorran", "AO": "Angolan", "AR": "Argentine|Argentinian",
 "AM": "Armenian", "AU": "Australian", "AT": "Austrian", "AZ": "Azerbaijani|Azerbaijan", "BH": "Bahraini", "BD": "Bangladeshi|Bangladesh",
 "BB": "Barbadian", "BY": "Belarusian|Belarus", "BE": "Belgian", "BZ": "Belizean", "BJ": "Beninese", "BT": "Bhutanese",
 "BO": "Bolivian", "BA": "Bosnian|Bosnia", "BW": "Botswana", "BR": "Brazilian", "BN": "Bruneian|Brunei Darussalam", "BG": "Bulgarian",
 "BF": "Burkinabe", "BI": "Burundian", "KH": "Cambodian", "CM": "Cameroonian", "CA": "Canadian", "CV": "Cape Verdean|Cape Verde|Cabo Verde",
 "CF": "Central African", "TD": "Chadian", "CL": "Chilean", "CN": "Chinese|People's Republic of China|Peoples Republic of China|Peoples' Republic of China|PR China", "CO": "Colombian",
 "KM": "Comorian", "CG": "Congo Brazzaville|Republic of Congo", "CD": "Democratic Republic of Congo|DR Congo|RD Congo|Congo Kinshasa",
 "CR": "Costa Rican", "CI": "Ivorian|Cote d Ivoire|Côte d'Ivoire|Ivory Coast", "HR": "Croatian", "CU": "Cuban", "CY": "Cypriot|Cyprus",
 "CZ": "Czech|Czechia|Czech Republic", "DK": "Danish|Royal Danish", "DJ": "Djiboutian", "DO": "Dominican Republic", "EC": "Ecuadorian",
 "EG": "Egyptian", "SV": "Salvadoran|Salvadorean", "GQ": "Equatoguinean|Equatorial Guinean", "ER": "Eritrean", "EE": "Estonian",
 "SZ": "Swazi|Eswatini|Swaziland", "ET": "Ethiopian", "FJ": "Fijian", "FI": "Finnish", "FR": "French", "GA": "Gabonese", "GM": "Gambian",
 "GE": "Georgian", "DE": "German|Federal Republic of Germany", "GH": "Ghanaian", "GR": "Greek|Hellenic", "GD": "Grenadian",
 "GT": "Guatemalan", "GN": "Guinean", "GW": "Bissau Guinean", "GY": "Guyanese", "HT": "Haitian", "HN": "Honduran", "HU": "Hungarian",
 "IS": "Icelandic", "IN": "Indian", "ID": "Indonesian", "IR": "Iranian|Islamic Republic of Iran", "IQ": "Iraqi", "IE": "Irish",
 "IL": "Israeli", "IT": "Italian", "JM": "Jamaican", "JP": "Japanese", "JO": "Jordanian|Hashemite Kingdom", "KZ": "Kazakh|Kazakhstani",
 "KE": "Kenyan", "KW": "Kuwaiti", "KG": "Kyrgyz", "LA": "Lao|Laotian", "LV": "Latvian", "LB": "Lebanese", "LS": "Basotho|Lesotho",
 "LR": "Liberian", "LY": "Libyan", "LT": "Lithuanian", "LU": "Luxembourgish|Luxembourg", "MG": "Malagasy", "MW": "Malawian",
 "MY": "Malaysian", "MV": "Maldivian", "ML": "Malian", "MT": "Maltese", "MR": "Mauritanian", "MU": "Mauritian", "MX": "Mexican",
 "MD": "Moldovan|Moldova", "MC": "Monegasque", "MN": "Mongolian", "ME": "Montenegrin", "MA": "Moroccan", "MZ": "Mozambican",
 "MM": "Myanmar|Burmese", "NA": "Namibian", "NP": "Nepalese|Nepali", "NL": "Dutch|Netherlands|Royal Netherlands", "NZ": "New Zealand",
 "NI": "Nicaraguan", "NE": "Nigerien", "NG": "Nigerian", "MK": "Macedonian|North Macedonia", "NO": "Norwegian|Royal Norwegian",
 "OM": "Omani", "PK": "Pakistani", "PA": "Panamanian", "PG": "Papua New Guinean", "PY": "Paraguayan", "PE": "Peruvian",
 "PH": "Philippine|Filipino", "PL": "Polish", "PT": "Portuguese", "QA": "Qatari", "RO": "Romanian", "RU": "Russian|Russian Federation",
 "RW": "Rwandan|Rwandese", "SA": "Saudi", "SN": "Senegalese", "RS": "Serbian", "SC": "Seychellois", "SL": "Sierra Leonean",
 "SG": "Singaporean", "SK": "Slovak", "SI": "Slovenian|Slovene", "SO": "Somali", "ZA": "South African", "SS": "South Sudanese",
 "ES": "Spanish", "LK": "Sri Lankan", "SD": "Sudanese", "SR": "Surinamese", "SE": "Swedish", "CH": "Swiss", "SY": "Syrian",
 "TJ": "Tajik|Tajikistani", "TZ": "Tanzanian", "TH": "Thai|Royal Thai", "TL": "Timorese|East Timor|Timor Leste", "TG": "Togolese",
 "TO": "Tongan", "TT": "Trinidad and Tobago", "TN": "Tunisian", "TR": "Turkish|Turkey|Türkiye|Turkiye", "TM": "Turkmen",
 "UG": "Ugandan", "UA": "Ukrainian", "AE": "Emirati|UAE|United Arab Emirates", "GB": "British|UK|United Kingdom|Great Britain",
 "US": "American|U.S.|USA|United States", "UY": "Uruguayan", "UZ": "Uzbek|Uzbekistani", "VU": "Ni-Vanuatu", "VE": "Venezuelan",
 "VN": "Vietnamese|Viet Nam", "YE": "Yemeni", "ZM": "Zambian", "ZW": "Zimbabwean", "KR": "Korean|Republic of Korea|South Korean",
 "KP": "North Korean|Democratic People's Republic of Korea|DPRK", "VA": "Holy See|Apostolic Nunciature|Apostolic|Nunciature|Nunziatura|Nonciature|Nunciatura|Vatican",
 "PS": "Palestinian|State of Palestine|Palestine", "TW": "Taipei|Taiwanese|Republic of China|Republic of China (Taiwan)|Republic of China Taiwan", "XK": "Kosovar|Kosovo", "WS": "Samoan",
 "SB": "Solomon Islands", "KI": "Kiribati", "TV": "Tuvaluan", "NR": "Nauruan", "PW": "Palauan", "MH": "Marshallese",
 "FM": "Micronesian", "AG": "Antiguan", "KN": "Kittitian", "LC": "Saint Lucian", "VC": "Vincentian", "DM": "Dominica",
 "BS": "Bahamian", "LI": "Liechtenstein", "SM": "Sammarinese|San Marino", "ST": "Sao Tome", "EH": "Sahrawi|SADR|Saharawi",
}
for k, v in ALT.items():
    S[k]["alt"] = set(v.split("|"))
for k in S:
    S[k].setdefault("alt", set())
NS = {"EU": {"European Union", "EU", "Union europeenne", "Europaische Union", "Union Europea", "Unione europea", "European Commission"},
      "XO": {"Order of Malta", "Sovereign Military Order of Malta", "Ordre de Malte", "Malteserorden", "Orden de Malta", "Ordine di Malta", "Sovereign Order of Malta"}}

# Name matcher: normalised strings -> code. Longest names first; a matched span is masked so "Niger" cannot match inside "Nigeria".
pat = []
for code, s in S.items():
    for n in s["names"] | s["alt"] | s["intl"]:
        if len(norm(n)) >= 3 or n in ("UK", "UAE", "US"):
            pat.append((norm(n), code))
for code, ns in NS.items():
    for n in ns:
        pat.append((norm(n), code))
bad = {"guinea": None}           # bare "guinea" is fine (Guinea), longer names win first
pat = sorted(set(pat), key=lambda t: -len(t[0]))
amb = {}
for n, c in pat:
    amb.setdefault(n, set()).add(c)
pat = [(n, c) for n, c in pat if len(amb[n]) == 1]
print("name patterns", len(pat), "ambiguous dropped", sum(1 for v in amb.values() if len(v) > 1))

# Capitals: Natural Earth admin-0 capitals; where a state has several, the seat of government where embassies sit.
PP = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
places = [{"name": f["properties"]["name"], "lat": f["properties"]["latitude"], "lon": f["properties"]["longitude"],
           "pop": f["properties"]["pop_max"], "iso": f["properties"]["iso_a2"], "cap": f["properties"]["adm0cap"],
           "fc": f["properties"]["featurecla"], "adm0": f["properties"]["adm0name"]} for f in PP]
SEAT = {"NL": "The Hague", "BO": "La Paz", "ZA": "Pretoria", "CI": "Abidjan", "TZ": "Dar es Salaam", "LK": "Colombo",
        "BJ": "Cotonou", "MY": "Kuala Lumpur", "MM": "Naypyidaw", "IL": "Jerusalem", "PS": "Ramallah", "CH": "Bern",
        "SZ": "Mbabane", "VA": "Vatican City", "XK": "Pristina", "TW": "Taipei", "PW": "Melekeok",
        "BI": "Bujumbura", "ME": "Podgorica", "FM": "Palikir", "KI": "Tarawa", "NR": "Yaren", "TV": "Funafuti",
        "MH": "Majuro", "SB": "Honiara", "SM": "San Marino", "LI": "Vaduz", "AD": "Andorra", "MC": "Monaco"}
# Official capitals named in constitutions or laws, used to compare with where embassies actually are.
OFFICIAL_CAPITAL = {"IL": "Jerusalem", "BO": "Sucre", "CI": "Yamoussoukro", "TZ": "Dodoma", "NL": "Amsterdam",
                    "LK": "Sri Jayawardenepura Kotte", "BJ": "Porto-Novo", "MM": "Naypyidaw", "MY": "Kuala Lumpur",
                    "BI": "Gitega", "PW": "Ngerulmud", "CH": "Bern", "NG": "Abuja", "KZ": "Astana", "BR": "Brasilia",
                    "PK": "Islamabad", "TR": "Ankara", "AU": "Canberra", "CA": "Ottawa", "US": "Washington", "ZA": "Pretoria"}
cap = {}
for code in STATES:
    nm = SEAT.get(code)
    cands = [p for p in places if (p["iso"] == code or (code == "XK" and p["adm0"] == "Kosovo") or (code == "PS" and p["adm0"] in ("Palestine", "West Bank"))
                                   or (code == "EH" and p["adm0"] == "Western Sahara") or (code == "TW" and p["adm0"] == "Taiwan"))]
    hit = None
    if nm:
        hit = [p for p in cands if p["name"] == nm] or [p for p in places if p["name"] == nm]
    if not hit:
        hit = [p for p in cands if p["cap"] == 1] or [p for p in cands if p["fc"].startswith("Admin-0")]
    if not hit:
        hit = sorted(cands, key=lambda p: -p["pop"])[:1]
    if not hit:     # no Natural Earth place (Nauru): the representative point of the territory
        g = max([u for u in units if u["state"] == code], key=lambda u: u["geom"].area)["geom"].representative_point()
        hit = [{"name": nm or S[code]["name"], "lat": g.y, "lon": g.x, "pop": 0}]
    h = max(hit, key=lambda p: p["pop"])
    cap[code] = {"name": "Vatican City" if code == "VA" else re.sub(r"\s+", " ", h["name"]), "lat": h["lat"], "lon": h["lon"]}
# The SADR's proclaimed capital lies in territory administered by Morocco and its institutions sit in exile; lines for it
# start from the middle of the territory, labelled as such, rather than from any city.
g = max([u for u in units if u["state"] == "EH"], key=lambda u: u["geom"].area)["geom"].representative_point()
cap["EH"] = {"name": "Western Sahara (territory)", "lat": g.y, "lon": g.x}
cap["EU"] = {"name": "Brussels", "lat": 50.8467, "lon": 4.3517}
cap["XO"] = {"name": "Rome", "lat": 41.9054, "lon": 12.4796}
for code in STATES:
    S[code]["capital"] = cap[code]

# country names for non-states
for k, v in NONSTATE.items():
    S[k] = {"code": k, "name": v, "pop": 0, "area_km2": 0, "continent": "", "subregion": "", "wd": None, "un": False,
            "names": NS[k], "intl": set(), "alt": set(), "capital": cap[k]}

tree = STRtree([u["geom"] for u in units])
pickle.dump({"S": S, "units": units, "pat": pat, "places": places, "official": OFFICIAL_CAPITAL}, open(f"{WORK}/countries.pkl", "wb"))
rows = [{"code": k, "name": v["name"], "un_member": v["un"], "population": v["pop"], "area_km2": v["area_km2"],
         "continent": v["continent"], "wikidata": v["wd"], "capital_or_seat": v["capital"]["name"],
         "capital_lat": round(v["capital"]["lat"], 4), "capital_lon": round(v["capital"]["lon"], 4)} for k, v in S.items()]
pd.DataFrame(rows).to_csv(f"{DATA}/countries.csv", index=False)
print(len(S), "states and entities;", sum(v["un"] for v in S.values()), "UN members")
