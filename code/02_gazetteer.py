"""Build the gazetteer of current missions from OpenStreetMap and Wikidata.

Steps: classify each OSM feature (type), resolve its sending state (country tag, linked Wikidata item, or its name),
place it in a host territory (Natural Earth), set its receiving state or organisation, give it a city; drop residences,
non-diplomatic objects and international-organisation offices; merge duplicates; then reconcile with Wikidata (drop the
wrong classes, add located items missing from OSM, keep unlocated embassies as country pairs only).
Outputs: data/missions.csv, data/missions.geojson, data/dyads.csv, WORK/gaz.pkl, data/merge_log.json."""
import pickle, csv
from collections import Counter, defaultdict
import pandas as pd
from shapely.geometry import Point
from shapely.strtree import STRtree
from common import *

C = pickle.load(open(f"{WORK}/countries.pkl", "rb"))
S, units, PAT, places = C["S"], C["units"], C["pat"], C["places"]
LOG = defaultdict(int)
EX = defaultdict(list)          # examples for the log

# ---------------- name matching ----------------
def find_codes(text):
    """All state codes named in a text, in order of appearance (longest names first, matched spans masked)."""
    if not text:
        return []
    t = " " + norm(text) + " "
    hits = []
    for n, c in PAT:
        i = t.find(" " + n + " ")
        while i >= 0:
            hits.append((i, c))
            t = t[:i + 1] + "#" * len(n) + t[i + 1 + len(n):]
            i = t.find(" " + n + " ")
    return [c for _, c in sorted(hits)]


KW = re.compile(r"embass|embaj|embaix|ambassad|ambasciat|botschaft|ambasad|velvysl|nagykov|veleposl|buyukelc|büyükelç|посольств|"
                r"سفار|大使|대사관|consul|konsul|konzul|konsolos|консульств|قنصل|領事|领事|영사|high commission|nunci|nunzi|nonci|nuntia|"
                r"mission|misi[oó]n|miss[aã]o|repr[eé]sentation|vertretung|delegat|d[eé]l[eé]gation|delegaci|legation|taipei|interests section|"
                r"office|bureau|oficina|ufficio|liaison|trade|economic", re.I)
HON = re.compile(r"honor|honour|honora|onorar|honorowy|honorárn|honorarn|fahri|почетн|почётн|فخري|名誉|명예", re.I)
CG = re.compile(r"consulate[\s-]*general|consulado[\s-]*general|consulat[\s-]*g[eé]n[eé]ral|generalkonsulat|consolato generale|"
                r"konsulat generaln|generalkonzul|başkonsolos|baskonsolos|генеральн|القنصلية العامة|总领事|總領事|総領事|총영사|consul general", re.I)
RES = re.compile(r"residen|reședin|resedin|residência|резиденц|官邸|公邸|관저|ambassador.?s house|chancery residence", re.I)
PM = re.compile(r"permanent (mission|representation|delegation)|mission permanente|repr[eé]sentation permanente|st[aä]ndige vertretung|"
                r"misi[oó]n permanente|missione permanente|miss[aã]o permanente|delegaci[oó]n permanente|stałe przedstawicielstwo", re.I)
HC = re.compile(r"high commission|haut[- ]commissariat|alto comisionado|hochkommissariat", re.I)
DEPUTY_HC = re.compile(r"(deputy|assistant) high commission", re.I)
SUBNAT = re.compile(r"qu[eé]bec|flanders|flandre|vlaanderen|wallon|catalu|catalonia|generalitat|bavari|bayern|scotland|scottish|"
                    r"basque|euskadi|tyrol|tirol|galicia|bangsamoro|hong kong|macao|macau|ontario|alberta|region of|state of [a-z]+ (in|to)|"
                    r"representation of [a-z]", re.I)
ORGKEY = [("UN", r"united nations|nations unies|naciones unidas|vereinten nationen|\bun\b|onu\b"), ("EU", r"european union|union europ|europäische union|europ[aä]ischen union|\beu\b"),
          ("COE", r"council of europe|conseil de l.europe|europarat"), ("OECD", r"oecd|ocde"), ("UNESCO", r"unesco"), ("NATO", r"nato|otan"),
          ("OSCE", r"osce"), ("WTO", r"wto|world trade"), ("FAO", r"fao\b"), ("AU_ORG", r"african union|union africaine"), ("ASEAN", r"asean"),
          ("OAS", r"organi[sz]ation of american states|\boas\b|\boea\b"), ("IAEA", r"iaea|vienna office")]
TGT_ORG = {"UN": "UN", "EU": "EU", "COE": "COE", "OECD": "OECD", "UNESCO": "UNESCO", "NATO": "NATO", "OSCE": "OSCE", "WTO": "WTO",
           "FAO": "FAO", "OAS": "OAS", "ASEAN": "ASEAN", "UNOG": "UN", "UNOV": "IAEA", "IAEA": "IAEA", "EUCO": "EU", "AU-ORG": "AU_ORG"}
INTL_SENDER = {"UN", "OEA", "OSCE", "UNTSO", "LAS", "COE", "OAS", "NATO", "OECD", "UNESCO", "WHO", "WB", "IMF", "AU_ORG", "ASEAN"}
NONSTATE_CODES = {"EU": "EU", "SMOM": "XO", "XOM": "XO", "XO": "XO"}


def org_from(text):
    t = norm(text)
    for code, rx in ORGKEY:
        if re.search(rx, t):
            return code
    return None


# ---------------- host territory ----------------
geoms = [u["geom"] for u in units]
tree = STRtree(geoms)


def locate(lat, lon):
    p = Point(lon, lat)
    for i in tree.query(p, predicate="intersects"):
        return units[i]
    i = tree.nearest(p)
    if geoms[i].distance(p) < 0.08:       # within about 8 km of a coast or border
        return units[i]
    return None


# ---------------- city ----------------
# Natural Earth lacks Ramallah, where most missions to Palestine sit; without it they would be named after Jerusalem.
places = places + [{"name": "Ramallah", "lat": 31.9038, "lon": 35.2034, "pop": 40000, "iso": "PS", "cap": 0, "fc": "Populated place", "adm0": "Palestine"}]
CITY_RENAME = {"Nur-Sultan": "Astana"}
PL = pd.DataFrame(places)
PLAT, PLON, PPOP = PL.lat.values, PL.lon.values, PL["pop"].values.astype(float)


def city_of(lat, lon):
    d = gc_km(lat, lon, PLAT, PLON)
    k = np.where(d < 30)[0]
    if not len(k):
        k = np.where(d < 60)[0]
        if not len(k):
            return None
    score = np.maximum(PPOP[k], 1000) / (d[k] + 2.5) ** 2
    j = k[np.argmax(score)]
    return int(j)


# ---------------- classify OSM ----------------
def classify(e):
    """Return (type, why) or (None, reason to drop)."""
    dip, emb, con, nm = e.get("diplomatic"), e.get("embassy"), e.get("consulate"), " ".join(filter(None, [e.get("name:en"), e.get("name")]))
    if e.get("office") != "diplomatic" and e.get("amenity") != "embassy":
        return None, "not diplomatic (office or amenity tag)"
    if dip in ("ambassadors_residence", "ambassador_residence", "residence", "residential") or emb in ("residence", "yes;residence") or con == "residence":
        return None, "residence"
    if nm and RES.search(nm) and not re.search(r"consul|embass", e.get("name:en") or "", re.I):
        return None, "residence"
    if dip in ("non_diplomatic", "administration", "دارالترجمه", "دفتر_ترجمه", "international_organization"):
        return None, "non-diplomatic office"
    if emb == "nunciature" or re.search(r"nunci|nunzi|nonci|nuntia", nm, re.I):
        return "nunciature", ""
    if emb == "interests_section" or re.search(r"interests section", nm, re.I):
        return "interests_section", ""
    if dip == "permanent_mission" or PM.search(nm) or (emb in ("mission", "yes;mission") and (org_from(e.get("target") or "") or org_from(nm))):
        return "perm_mission", ""
    if emb == "branch_embassy" or dip in ("trade_delegation", "trade_commissioner_office", "trade_mission", "embassy=branch_embassy"):
        if re.search(r"taipei|teco|tecro", nm, re.I):
            return "liaison", ""
        return "embassy_office", ""
    if dip in ("liaison", "representative_office", "mission"):
        return "liaison", ""
    if emb == "delegation":
        return "delegation", ""
    if con in ("honorary_consul", "honorary_consulate") or (HON.search(nm) and dip != "embassy"):
        return "honorary", ""
    if HON.search(nm) and dip == "embassy" and re.search(r"consul|konsul|konzul", nm, re.I):
        return "honorary", ""
    if dip in ("consulate", "consulate;embassy") or con in ("consulate_general", "consular_office", "consular_agency", "yes"):
        if DEPUTY_HC.search(nm):
            return "consulate_general", ""
        if con == "consulate_general" or CG.search(nm):
            return "consulate_general", ""
        if dip == "embassy":
            return "embassy", ""
        return "consulate", ""
    if dip in ("embassy", "embassy;consulate") or emb in ("yes", "high_commission", "yes;mission", "mission", "internat") or e.get("amenity") == "embassy":
        if emb == "high_commission" or (HC.search(nm) and not DEPUTY_HC.search(nm)):
            return "high_commission", ""
        if DEPUTY_HC.search(nm):
            return "consulate_general", ""
        if emb == "mission":
            return "liaison", ""
        if re.search(r"consul|konsul|konzul", e.get("name:en") or e.get("name") or "", re.I) and not re.search(r"embass|botschaft|ambassad|embaj|embaix", nm, re.I):
            return ("consulate_general" if CG.search(nm) else "consulate"), ""
        return "embassy", ""
    if dip is None and nm and KW.search(nm):
        if re.search(r"consul|konsul|konzul", nm, re.I):
            return ("consulate_general" if CG.search(nm) else "consulate"), ""
        if re.search(r"embass|botschaft|ambassad|embaj|embaix|ambasciat|посольств|سفار|大使", nm, re.I):
            return ("high_commission" if HC.search(nm) else "embassy"), ""
        return "liaison", ""
    return None, "no diplomatic type"


# ---------------- Wikidata ----------------
WDF = pd.read_csv(WD, sep="\t", dtype=str, quoting=3).fillna("")
cls = {}
for t, g in WDF.groupby("type"):
    lab = g.label.str.contains(r"embass|consul|high commission|legation|nunciat|representat|taipei|liaison|interests section|mission|delegation", case=False)
    cls[t] = {"n": int(g.qid.nunique()), "share_named_as_mission": round(float(lab.mean()) * 100, 1)}
KEEP_CLASS = {"Q3917681": "embassy", "Q7843791": "consulate", "Q5244910": "liaison"}
for t in ("Q2385804", "Q2001305"):
    assert cls[t]["share_named_as_mission"] < 1, cls[t]
print("Wikidata classes:", cls)
QS = {u["wd"]: u["state"] for u in units if u.get("wd") and u["state"]}      # territories count under their state
QS.update({S[k]["wd"]: k for k in S if S[k].get("wd")})
QS.update({"Q29999": "NL", "Q756617": "DK", "Q219060": "PS", "Q40362": "EH", "Q159583": "VA", "Q190353": "XO", "Q458": "EU",
           "Q148": "CN", "Q865": "TW", "Q1246": "XK", "Q237": "VA", "Q30": "US", "Q145": "GB", "Q142": "FR", "Q183": "DE",
           "Q1231": "XK", "Q427941": "AF", "Q15180": None, "Q12560": None})
WDF = WDF.drop_duplicates("qid")
wdrows = {}
for r in WDF.itertuples():
    if r.type not in KEEP_CLASS:
        LOG["wd_dropped_wrong_class"] += 1
        continue
    if r.dissolved:
        LOG["wd_dropped_dissolved"] += 1
        continue
    snd = QS.get(r.op) if r.op else None
    rcv = QS.get(r.host) if r.host else None
    codes = find_codes(r.label)
    if not snd and codes:
        snd = codes[0]; LOG["wd_sender_from_label"] += 1
    if not rcv and len(codes) > 1:
        rcv = codes[1]; LOG["wd_receiver_from_label"] += 1
    if re.search(r"holy see|vatican", r.label, re.I) and snd != "VA":
        rcv = "VA"
    if (r.op and not snd) or (r.host and not rcv):
        LOG["wd_dropped_historical_or_unmapped_state"] += 1
        EX["wd_unmapped"].append(r.label)
        continue
    if not snd or not rcv or snd == rcv:
        LOG["wd_dropped_no_sender_or_receiver"] += 1
        continue
    lat = lon = None
    if r.coord.startswith("Point("):
        lon, lat = map(float, r.coord[6:-1].split())
    typ = KEEP_CLASS[r.type]
    if typ == "embassy" and HC.search(r.label) and not DEPUTY_HC.search(r.label):
        typ = "high_commission"
    if typ == "embassy" and re.search(r"nunci", r.label, re.I):
        typ = "nunciature"
    if typ == "consulate" and (CG.search(r.label) or DEPUTY_HC.search(r.label)):
        typ = "consulate_general"
    if typ == "consulate" and HON.search(r.label):
        typ = "honorary"
    if typ == "embassy" and re.search(r"consul", r.label, re.I) and not re.search(r"embass", r.label, re.I):
        typ = "consulate_general" if CG.search(r.label) else "consulate"
    if snd == "TW" and typ == "embassy" and re.search(r"taipei|economic|cultural|trade", r.label, re.I):
        typ = "liaison"
    yr = int(r.inception[:4]) if re.match(r"^\d{4}", r.inception) else None
    wdrows[r.qid] = {"qid": r.qid, "label": r.label, "type": typ, "sender": snd, "receiver": rcv, "lat": lat, "lon": lon, "year": yr}
print("Wikidata kept", len(wdrows), Counter(w["type"] for w in wdrows.values()))

# ---------------- OSM ----------------
OSMF = jload(OSM)
recs = []
for e in OSMF:
    LOG["osm_features"] += 1
    typ, why = classify(e)
    if not typ:
        LOG["osm_dropped: " + why] += 1
        continue
    u = locate(e["lat"], e["lon"])
    if not u or not u["state"]:
        LOG["osm_dropped: outside any territory"] += 1
        continue
    host = u["state"]
    name = e.get("name:en") or e.get("name") or ""
    allnames = " ; ".join(filter(None, [e.get("name:en"), e.get("name")]))
    raw = (e.get("country") or "").strip()
    tok = [t.strip() for t in re.split(r"[;,]", raw) if t.strip()]
    snd, sub, how = None, False, ""
    if tok:
        t0 = tok[0].upper()
        if t0 in INTL_SENDER or "CESAO" in t0 or t0 == "UN":
            LOG["osm_dropped: international organisation office"] += 1
            continue
        if t0 in NONSTATE_CODES:
            snd, how = NONSTATE_CODES[t0], "tag"
        elif re.fullmatch(r"[A-Z]{2}", t0) and t0 in S:
            snd, how = t0, "tag"
        elif re.fullmatch(r"[A-Z]{2}-[A-Z0-9]{1,3}", t0) and t0[:2] in S:
            snd, sub, how = t0[:2], True, "tag"
        elif t0 == "HK":
            snd, sub, how = "CN", True, "tag"
        elif t0 in ("TRNC", "NCY"):
            LOG["osm_dropped: unrecognised-entity sender (Northern Cyprus)"] += 1
            continue
        else:
            cc = find_codes(raw)
            if cc:
                snd, how = cc[0], "tag name"
    if not snd and e.get("wikidata") in wdrows:
        snd, how = wdrows[e["wikidata"]]["sender"], "wikidata"
    if snd == host and typ != "perm_mission":
        LOG["osm_sender_equal_host_checked"] += 1
        snd = None
    if not snd:
        cc = [c for c in find_codes(allnames) if c != host]
        if cc and not (cc[0] == "TW" and not re.search(r"taiwan|taipei|台", allnames, re.I)):   # a bare "Republic of China" is ambiguous
            snd, how = cc[0], "name"
    if not snd:
        if KW.search(allnames):
            LOG["osm_dropped: sender unknown"] += 1
            EX["sender_unknown"].append(allnames)
        else:
            LOG["osm_dropped: no sender, no diplomatic name"] += 1
        continue
    if SUBNAT.search(allnames) and snd in S and not (snd == "CN" and "hong kong" not in allnames.lower() and "macao" not in allnames.lower() and "macau" not in allnames.lower()):
        if not re.search(r"embassy of|consulate|high commission", e.get("name:en") or "", re.I) or re.search(r"qu[eé]bec|flanders|wallon|catalon|bavaria|scotland|hong kong", allnames, re.I):
            sub = True
    if snd in ("US", "GB") and re.search(r"united nations|\bun\b", norm(allnames)) and typ == "liaison":
        LOG["osm_dropped: international organisation office"] += 1
        continue
    # receiving state or organisation
    tg = [t.strip().upper() for t in re.split(r"[;,]", e.get("target") or "") if t.strip()]
    rcv = host
    if typ == "perm_mission":
        rcv = next((TGT_ORG[t] for t in tg if t in TGT_ORG), None) or org_from(allnames) or "INTL"
    elif snd != "VA" and (tg[:1] == ["VA"] or re.search(r"holy see|santa sede|saint[- ]si[eè]ge|heiliger? stuhl|stolica apostolska|vatican", allnames, re.I)) and host in ("IT", "VA"):
        rcv = "VA"
    elif typ in ("embassy", "high_commission", "delegation") and (tg[:1] in (["EU"], ["EUCO"]) or re.search(r"to the european union|aupr[eè]s de l.union europ|bei der europ", allnames, re.I)) and snd != "EU":
        typ, rcv = "perm_mission", "EU"
    if typ == "perm_mission" and rcv in S and rcv != "EU":
        typ = "embassy"
    if snd == rcv:
        LOG["osm_dropped: sender equals receiver"] += 1
        continue
    if snd == "TW" and typ in ("embassy", "consulate", "consulate_general") and re.search(r"taipei|economic|cultural|trade|representative", allnames, re.I):
        typ = "liaison"
    if snd == "VA" and typ == "embassy":
        typ = "nunciature"
    if snd == "EU" and typ in ("embassy", "liaison", "high_commission"):
        typ = "delegation"
    if sub:
        LOG["osm_subnational_kept_separately"] += 1
    ci = city_of(e["lat"], e["lon"])
    recs.append({"id": e["id"], "src": "osm", "name": name, "name_local": e.get("name") or "", "type": typ, "sender": snd, "receiver": rcv,
                 "host": host, "unit": u["unit"], "lat": round(e["lat"], 6), "lon": round(e["lon"], 6), "city_i": ci,
                 "addr_city": e.get("addr:city") or "", "wikidata": e.get("wikidata") or "", "website": e.get("website") or "",
                 "sender_from": how, "subnational": sub, "tags": sum(1 for k in e if k not in ("id", "lat", "lon"))})
print("OSM kept before merging", len(recs))

# ---------------- checks and corrections ----------------
# 1. An explicit English name ("Embassy of Montenegro") beats a conflicting country tag.
EXPL = re.compile(r"^(?:the )?(?:embassy|consulate[ -]general|consulate|high commission|permanent mission|honorary consulate|apostolic nunciature)"
                  r" of (?:the )?(.+?)(?: in | to |,|$)", re.I)
for r in recs:
    mm = EXPL.match(r["name"] if r["sender_from"] == "tag" else "")
    if not mm:
        continue
    cc = [c for c in find_codes(mm.group(1)) if c != r["host"]]
    if len(set(cc)) == 1 and cc[0] != r["sender"] and cc[0] in S and r["sender"] != "XO" and {cc[0], r["sender"]} not in ({"KP", "KR"}, {"CN", "TW"}) \
            and r["type"] != "interests_section" and "interests" not in r["name"].lower():
        EX["name_overrides_tag"].append(f"{r['name']}: tag {r['sender']} -> {cc[0]}")
        r["sender"], r["sender_from"] = cc[0], "name over tag"
        LOG["osm_sender_corrected_from_name"] += 1
# 2. Taiwan: twelve states recognise it (Reuters factbox, 2026: "Taiwan's 12 remaining diplomatic allies"). Embassy-level
# records between Taiwan and any other state are either working offices named as embassies (made liaison offices) or
# out-of-date records of embassies closed when recognition switched (flagged and left out of all counts).
TW_ALLIES = {"BZ", "GT", "HT", "PY", "KN", "LC", "VC", "MH", "PW", "TV", "SZ", "VA"}
FLAG = []
def tw_fix(r, label):
    other = r["receiver"] if r["sender"] == "TW" else r["sender"] if r["receiver"] == "TW" else None
    if other is None or other in TW_ALLIES or TYPES[r["type"]][1] not in ("resident", "consular"):
        return True
    if re.search(r"\bembassy\b|embajada|ambassade|大使館", label, re.I) and r["type"] == "embassy":
        r["flag"] = "Taiwan embassy record in a state that no longer recognises Taiwan (record out of date)"
        LOG["flagged_out_of_date_taiwan"] += 1
        return False
    r["type"] = "liaison"; LOG["taiwan_offices_reclassified_liaison"] += 1
    return True
keep = []
for r in recs:
    (keep if tw_fix(r, r["name"] + " " + r["name_local"]) else FLAG).append(r)
recs = keep
# 3. Hand corrections, each with its reason (also in data/merge_log.json).
CORR = [
    (lambda r: r["host"] == "XK" and r["sender"] in ("RU", "CN") and r["type"] == "embassy", {"type": "liaison"},
     "Russia and China do not recognise Kosovo; their offices in Pristina are liaison offices (the Chinese one is mapped as an embassy office)"),
    (lambda r: r["sender"] == "EU" and r["receiver"] == "IL" and gc_km(31.778, 35.225, r["lat"], r["lon"]) < 8, {"receiver": "PS"},
     "the EU office in Jerusalem is the Office of the EU Representative for the West Bank and Gaza; the EU delegation to Israel is in Ramat Gan"),
]
for r in recs:
    for f, ch, why in CORR:
        if f(r):
            r.update(ch); LOG["hand_corrections"] += 1; EX["hand_corrections"].append(f"{r['name']} ({r['sender']} in {r['host']}): {why}")

# ---------------- merge duplicates ----------------
GRP = {k: v[1] for k, v in TYPES.items()}
def gkey(r):
    return (r["sender"], r["receiver"], GRP[r["type"]], r["subnational"])
by = defaultdict(list)
for i, r in enumerate(recs):
    by[gkey(r)].append(i)
parent = list(range(len(recs)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for k, ix in by.items():
    if len(ix) < 2:
        continue
    la = np.array([recs[i]["lat"] for i in ix]); lo = np.array([recs[i]["lon"] for i in ix])
    for a in range(len(ix)):
        d = gc_km(la[a], lo[a], la, lo)
        for b in np.where(d < 0.35)[0]:
            if b > a:
                parent[find(ix[b])] = find(ix[a])
qid_first = {}
for i, r in enumerate(recs):
    if r["wikidata"]:
        if r["wikidata"] in qid_first and recs[qid_first[r["wikidata"]]]["sender"] == r["sender"]:
            j = qid_first[r["wikidata"]]
            if gc_km(r["lat"], r["lon"], recs[j]["lat"], recs[j]["lon"]) < 3:
                parent[find(i)] = find(j)
        else:
            qid_first[r["wikidata"]] = i
groups = defaultdict(list)
for i in range(len(recs)):
    groups[find(i)].append(i)
rank = {t: k for k, t in enumerate(TYPE_ORDER)}
M = []
for g in groups.values():
    rs = [recs[i] for i in g]
    best = max(rs, key=lambda r: (bool(r["wikidata"]), r["tags"], r["id"][0] == "n"))
    m = dict(best)
    m["type"] = min((r["type"] for r in rs), key=lambda t: rank[t])
    m["merged"] = [r["id"] for r in rs if r["id"] != best["id"]]
    for k in ("wikidata", "website", "addr_city"):
        if not m[k]:
            m[k] = next((r[k] for r in rs if r[k]), "")
    M.append(m)
LOG["osm_merged_duplicates"] = len(recs) - len(M)
print("OSM missions after merging", len(M))

# ---------------- reconcile with Wikidata ----------------
osm_q = {m["wikidata"]: m for m in M if m["wikidata"]}
dy_osm = defaultdict(list)
for m in M:
    if not m["subnational"]:
        dy_osm[(m["sender"], m["receiver"])].append(m)
added, unlocated = 0, []
for q, w in wdrows.items():
    if q in osm_q:
        m = osm_q[q]
        m["wd_year"] = w["year"]
        LOG["wd_linked_by_osm_tag"] += 1
        continue
    same = dy_osm.get((w["sender"], w["receiver"]), [])
    if w["lat"] is not None:
        near = [m for m in same if gc_km(w["lat"], w["lon"], m["lat"], m["lon"]) < 3]
        if near:
            near[0].setdefault("wd_year", w["year"]); near[0]["wikidata"] = near[0]["wikidata"] or q
            LOG["wd_matched_by_place"] += 1
            continue
        u = locate(w["lat"], w["lon"])
        if not u:
            LOG["wd_dropped_bad_coordinates"] += 1
            continue
        if w["type"] in ("embassy", "high_commission", "nunciature") and any(TYPES[m["type"]][1] == "resident" for m in same):
            LOG["wd_matched_by_pair_other_place"] += 1      # same embassy, coordinates disagree (old building or rough point)
            continue
        if w["type"] in ("embassy", "high_commission", "nunciature") and u["state"] != w["receiver"] and w["receiver"] != "VA":
            LOG["wd_dropped_coordinates_outside_receiver"] += 1
            continue
        M.append({"id": q, "src": "wikidata", "name": w["label"], "name_local": "", "type": w["type"], "sender": w["sender"],
                  "receiver": w["receiver"], "host": u["state"], "unit": u["unit"], "lat": round(w["lat"], 6), "lon": round(w["lon"], 6),
                  "city_i": city_of(w["lat"], w["lon"]), "addr_city": "", "wikidata": q, "website": "", "sender_from": "wikidata",
                  "subnational": False, "tags": 0, "merged": [], "wd_year": w["year"]})
        added += 1
        continue
    if same and (w["type"] not in ("embassy", "high_commission", "nunciature") or any(TYPES[m["type"]][1] == "resident" for m in same)):
        LOG["wd_matched_by_pair"] += 1
        for m in same:
            if TYPES[m["type"]][1] == TYPES[w["type"]][1] and w["year"]:
                m.setdefault("wd_year", w["year"])
        continue
    unlocated.append(w)
unl2 = []
for w in unlocated:
    r = {"sender": w["sender"], "receiver": w["receiver"], "type": w["type"], "name": w["label"], "name_local": ""}
    if tw_fix(r, w["label"]):
        w["type"] = r["type"]; unl2.append(w)
    else:
        FLAG.append(dict(w, flag=r["flag"]))
unlocated = unl2
LOG["wd_added_located"] = added
LOG["wd_unlocated_pairs"] = len(unlocated)
print("added from Wikidata (located)", added, "; unlocated", len(unlocated), Counter(w["type"] for w in unlocated))

# ---------------- city names and output ----------------
for m in M:
    p = places[m["city_i"]] if m["city_i"] is not None else None
    m["city"] = CITY_RENAME.get(p["name"], re.sub(r"\s+", " ", p["name"])) if p else (m["addr_city"] or "")
    m["city_lat"] = p["lat"] if p else m["lat"]; m["city_lon"] = p["lon"] if p else m["lon"]
    m.setdefault("wd_year", None)
M.sort(key=lambda m: (m["host"], m["city"], m["sender"], rank[m["type"]]))
cols = ["id", "src", "type", "sender", "receiver", "host", "unit", "city", "lat", "lon", "name", "name_local", "wikidata", "website",
        "wd_year", "sender_from", "subnational", "merged"]
with open(f"{DATA}/missions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(cols[:4] + ["sender_name", "receiver_name"] + cols[4:])
    for m in M:
        rn = S[m["receiver"]]["name"] if m["receiver"] in S else ORGS[m["receiver"]][0]
        w.writerow([m["id"], m["src"], m["type"], m["sender"], S[m["sender"]]["name"], rn] + [m[c] if c != "merged" else ";".join(m[c]) for c in cols[4:]])
gj = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [m["lon"], m["lat"]]},
      "properties": {k: m[k] for k in ("id", "src", "type", "sender", "receiver", "host", "city", "name", "wikidata", "wd_year", "subnational")}} for m in M]}
jsave(gj, f"{DATA}/missions.geojson")
with open(f"{DATA}/wikidata_unlocated.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["qid", "label", "type", "sender", "receiver", "inception_year"])
    for x in sorted(unlocated, key=lambda x: (x["sender"], x["receiver"])):
        w.writerow([x["qid"], x["label"], x["type"], x["sender"], x["receiver"], x["year"] or ""])
LOG["missions_total"] = len(M)
with open(f"{DATA}/flagged_out_of_date.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["id", "name", "sender", "receiver", "type", "reason"])
    for x in FLAG:
        w.writerow([x.get("id") or x.get("qid"), x.get("name") or x.get("label"), x["sender"], x["receiver"], x["type"], x["flag"]])
log = {"counts": dict(sorted(LOG.items())), "wikidata_classes": cls, "examples": {k: v[:40] for k, v in EX.items()}}
jsave(log, f"{DATA}/merge_log.json", indent=1)
pickle.dump({"M": M, "unlocated": unlocated, "flagged": FLAG, "wd": wdrows, "log": dict(LOG), "cls": cls}, open(f"{WORK}/gaz.pkl", "wb"))
print(json.dumps(dict(sorted(LOG.items())), indent=0))
print(Counter(m["type"] for m in M))
