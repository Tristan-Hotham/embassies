"""Page data: data/points.json (every mission, columnar), data/site.json (countries, their values and coverage notes,
unlocated pairs, cities for search) and data/world.json (simplified Natural Earth 50m outlines keyed by state code)."""
import pickle
from collections import Counter, defaultdict
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from common import *

C = pickle.load(open(f"{WORK}/countries.pkl", "rb")); G = pickle.load(open(f"{WORK}/gaz.pkl", "rb")); Q = pickle.load(open(f"{WORK}/res.pkl", "rb"))
S = C["S"]; M = G["M"]; UNL = G["unlocated"]; CS = Q["CS"].set_index("code")
R = jload(f"{DATA}/results.json")

codes = STATES + list(NONSTATE) + list(ORGS)
ci = {c: i for i, c in enumerate(codes)}
cities = sorted({m["city"] for m in M if m["city"]})
cix = {c: i for i, c in enumerate(cities)}
tix = {t: i for i, t in enumerate(TYPE_ORDER)}
P = {"codes": codes, "types": TYPE_ORDER, "cities": cities, "lat": [], "lon": [], "t": [], "s": [], "r": [], "h": [], "c": [], "n": [], "id": [], "f": []}
for m in M:
    P["lat"].append(round(m["lat"], 5)); P["lon"].append(round(m["lon"], 5)); P["t"].append(tix[m["type"]]); P["s"].append(ci[m["sender"]])
    P["r"].append(ci[m["receiver"]]); P["h"].append(ci[m["host"]]); P["c"].append(cix.get(m["city"], -1))
    P["n"].append(m["name"][:90]); P["id"].append(m["id"])
    P["f"].append((1 if m["src"] == "wikidata" else 0) | (2 if m["subnational"] else 0))
jsave(P, f"{DATA}/points.json")

# countries
site = {"codes": codes, "c": {}}
unl = defaultdict(list)
for w in UNL:
    unl[w["sender"]].append([ci[w["receiver"]], tix[w["type"]], w["label"][:90]])
for c in STATES + list(NONSTATE):
    s = S[c]
    row = CS.loc[c] if c in CS.index else None
    o = {"n": s["name"], "cap": [round(s["capital"]["lat"], 3), round(s["capital"]["lon"], 3), s["capital"]["name"]], "pop": int(s["pop"]),
         "un": bool(s["un"]), "u": unl.get(c, [])}
    if row is not None:
        o.update({"ea": int(row.embassies_abroad), "eh": int(row.embassies_hosted), "ma": int(row.missions_abroad_all), "mh": int(row.missions_hosted_all),
                  "ho": int(row.honorary_abroad), "po": int(row.posts), "dc": row.diplomatic_city, "dcn": int(row.diplomatic_city_n),
                  "cs": None if row.cow2005_abroad != row.cow2005_abroad else int(row.cow2005_abroad),
                  "ch": None if row.cow2005_hosted != row.cow2005_hosted else int(row.cow2005_hosted),
                  "ca": row.coverage_abroad, "cH": row.coverage_hosted, "note": row.coverage_note})
        if o["dc"]:      # draw lines from where most embassies to the state are, if that is a city; else the capital
            pts = [m for m in M if m["receiver"] == c and m["city"] == o["dc"] and TYPES[m["type"]][1] == "resident"]
            if len(pts) >= 3 and c not in ("IL", "VA"):
                o["dcll"] = [round(float(np.median([m["city_lat"] for m in pts])), 3), round(float(np.median([m["city_lon"] for m in pts])), 3)]
    site["c"][c] = o
site["orgs"] = {k: v[0] for k, v in ORGS.items()}
site["typeNames"] = {k: v[0] for k, v in TYPES.items()}
site["typeGroup"] = {k: v[1] for k, v in TYPES.items()}
site["typeCol"] = TCOL
cc = Counter((m["city"], m["host"]) for m in M if m["city"])
pos = defaultdict(list)
for m in M:
    if m["city"]:
        pos[(m["city"], m["host"])].append((m["city_lat"], m["city_lon"]))
site["cityList"] = [[c, h, n, round(pos[(c, h)][0][0], 3), round(pos[(c, h)][0][1], 3)] for (c, h), n in cc.most_common() if n >= 2]
site["flagged"] = [[x["sender"], x["receiver"], x.get("name") or x.get("label")] for x in G["flagged"]]
jsave(site, f"{DATA}/site.json")

# outlines: Natural Earth 50m, each unit keyed by its state if it is that state's home territory, else unkeyed (grey)
NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]
FIX = {"PSX": "PS", "SAH": "EH", "KOS": "XK", "TWN": "TW", "VAT": "VA"}
feats = []
def rnd(g):
    def r(c):
        if isinstance(c[0], (float, int)):
            return [round(c[0], 2), round(c[1], 2)]
        return [r(x) for x in c]
    m = mapping(g); return {"type": m["type"], "coordinates": r(m["coordinates"])}
for f in NE:
    p = f["properties"]; iso = p["ISO_A2_EH"]; a3 = p["ADM0_A3"]
    key = FIX.get(a3) or (iso if iso in STATES and p["TYPE"] in ("Sovereign country", "Country", "Sovereignty", "Disputed") and a3 not in ("FLK", "GIB", "IOT") else None)
    g = shape(f["geometry"]).simplify(0.025, preserve_topology=True)
    if g.is_empty:
        continue
    feats.append({"type": "Feature", "properties": {"k": key, "u": p["NAME_EN"]}, "geometry": rnd(g)})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
for fn in ("points.json", "site.json", "world.json", "cow_timeline.json"):
    print(fn, os.path.getsize(f"{DATA}/{fn}") // 1024, "KB")

# today's embassy-level network for the last frame of the timeline (capital to capital, each unordered pair once)
tp, seen = [], set()
for a, b in sorted(Q["uni"]):
    k = tuple(sorted((a, b)))
    if k in seen or a not in S or b not in S:
        continue
    seen.add(k)
    A, B = S[a]["capital"], S[b]["capital"]
    tp.append([round(A["lat"], 2), round(A["lon"], 2), round(B["lat"], 2), round(B["lon"], 2), int((b, a) in Q["uni"])])
jsave({"pairs": tp}, f"{DATA}/today_pairs.json")
print("today pairs", len(tp), os.path.getsize(f"{DATA}/today_pairs.json") // 1024, "KB")
