"""Every number quoted anywhere: data/results.json. Also data/dyads.csv (state pairs), data/country_summary.csv
(per-country counts and coverage notes) and WORK/res.pkl for the site and figures."""
import pickle, csv
from collections import Counter, defaultdict
import pandas as pd
from shapely.ops import unary_union
from common import *

C = pickle.load(open(f"{WORK}/countries.pkl", "rb")); G = pickle.load(open(f"{WORK}/gaz.pkl", "rb")); W = pickle.load(open(f"{WORK}/cow.pkl", "rb"))
S, units, OFF = C["S"], C["units"], C["official"]
M, UNL, LOG = G["M"], G["unlocated"], G["log"]
GRP = {k: v[1] for k, v in TYPES.items()}
R = {"meta": {"page": PAGE, "repo": REPO, "year": 2026}}
ST = set(STATES)
cname = lambda c: S[c]["name"] if c in S else ORGS[c][0]

# ---------------- totals ----------------
state_m = [m for m in M if not m["subnational"] and m["sender"] in S]
R["data"] = {"osm_features": LOG["osm_features"], "missions": len(M), "missions_states": sum(1 for m in M if not m["subnational"] and m["sender"] in ST),
             "missions_eu": sum(1 for m in M if m["sender"] == "EU"), "missions_xo": sum(1 for m in M if m["sender"] == "XO"),
             "subnational": sum(1 for m in M if m["subnational"]), "from_osm": sum(1 for m in M if m["src"] == "osm"),
             "from_wikidata": sum(1 for m in M if m["src"] == "wikidata"), "merged_dups": LOG["osm_merged_duplicates"],
             "dropped_residences": LOG["osm_dropped: residence"], "dropped_unknown_sender": LOG["osm_dropped: sender unknown"],
             "dropped_intl_org": LOG["osm_dropped: international organisation office"],
             "dropped_other": sum(v for k, v in LOG.items() if k.startswith("osm_dropped")) - LOG["osm_dropped: residence"] - LOG["osm_dropped: sender unknown"] - LOG["osm_dropped: international organisation office"],
             "sender_from_name": sum(1 for m in M if m["sender_from"] == "name"), "osm_with_wikidata": sum(1 for m in M if m["src"] == "osm" and m["wikidata"]),
             "wd_kept": len(G["wd"]), "wd_linked": LOG.get("wd_linked_by_osm_tag", 0), "wd_matched": LOG.get("wd_matched_by_pair", 0) + LOG.get("wd_matched_by_place", 0) + LOG.get("wd_matched_by_pair_other_place", 0),
             "wd_added": LOG.get("wd_added_located", 0), "wd_unlocated": len(UNL), "wd_unlocated_embassy": sum(1 for w in UNL if GRP[w["type"]] == "resident"),
             "wd_dropped_dissolved": LOG.get("wd_dropped_dissolved", 0), "wd_wrong_class": LOG.get("wd_dropped_wrong_class", 0),
             "wd_classes": G["cls"], "by_type": {t: sum(1 for m in M if m["type"] == t) for t in TYPE_ORDER},
             "cities": len({(m["host"], m["city"]) for m in M}), "senders": len({m["sender"] for m in state_m if m["sender"] in ST}),
             "hosts": len({m["host"] for m in M})}
R["data"]["resident_located"] = sum(R["data"]["by_type"][t] for t in TYPE_ORDER if GRP[t] == "resident")
R["data"]["consular_located"] = R["data"]["by_type"]["consulate_general"] + R["data"]["by_type"]["consulate"]

# ---------------- pairs ----------------
pair = defaultdict(lambda: {"types": Counter(), "osm": 0, "wd": 0, "wd_unloc": 0, "cities": set()})
for m in M:
    if m["subnational"] or m["sender"] not in S or m["receiver"] not in S:
        continue
    p = pair[(m["sender"], m["receiver"])]
    p["types"][m["type"]] += 1; p["cities"].add(m["city"])
    p["osm" if m["src"] == "osm" else "wd"] += 1
    if m["wikidata"]:
        p["wd"] += 1
for w in UNL:
    if w["receiver"] in S:
        p = pair[(w["sender"], w["receiver"])]; p["types"][w["type"]] += 1; p["wd_unloc"] += 1; p["wd"] += 1
def level(p):
    g = {GRP[t] for t in p["types"]}
    for k in ("resident", "consular", "liaison", "honorary", "office", "multilateral"):
        if k in g:
            return k
res_pairs = {k for k, p in pair.items() if level(p) == "resident"}
with open(f"{DATA}/dyads.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["sender", "sender_name", "receiver", "receiver_name", "highest_level", "embassy_level", "consular", "honorary", "liaison",
                "located_osm", "located_wikidata", "wikidata_unlocated", "cities", "cow_2005_represented"])
    for (a, b), p in sorted(pair.items()):
        t = p["types"]
        w.writerow([a, cname(a), b, cname(b), level(p), sum(t[x] for x in t if GRP[x] == "resident"), sum(t[x] for x in t if GRP[x] == "consular"),
                    t["honorary"], t["liaison"], p["osm"], sum(1 for _ in [0]) * 0 + (p["wd"] - p["wd_unloc"] if p["wd"] > p["wd_unloc"] else 0),
                    p["wd_unloc"], ";".join(sorted(c for c in p["cities"] if c)), int((a, b) in W["rep05"])])
# agreement between sources for embassy-level pairs among states
osm_res = {(m["sender"], m["receiver"]) for m in M if m["src"] == "osm" and GRP[m["type"]] == "resident" and not m["subnational"] and m["sender"] in ST and m["receiver"] in ST}
wd_res = {(w["sender"], w["receiver"]) for w in G["wd"].values() if GRP[w["type"]] == "resident" and w["sender"] in ST and w["receiver"] in ST}
uni = {k for k in res_pairs if k[0] in ST and k[1] in ST}
R["pairs"] = {"resident_states": len(uni), "osm": len(osm_res), "wd": len(wd_res), "both": len(osm_res & wd_res), "osm_only": len(osm_res - wd_res),
              "wd_only": len(wd_res - osm_res), "possible": len(ST) * (len(ST) - 1),
              "any_level_states": sum(1 for (a, b) in pair if a in ST and b in ST)}
R["pairs"]["density_pc"] = round(100 * R["pairs"]["resident_states"] / R["pairs"]["possible"], 1)
R["pairs"]["mutual"] = sum(1 for (a, b) in uni if (b, a) in uni) // 2
R["pairs"]["one_way"] = sum(1 for (a, b) in uni if (b, a) not in uni)

# ---------------- per country ----------------
abroad_res = Counter(a for a, b in uni); hosted_res = Counter(b for a, b in uni)
abroad_all = Counter(m["sender"] for m in M if not m["subnational"]); hosted_all = Counter(m["receiver"] if m["receiver"] in S else m["host"] for m in M)
honor = Counter(m["sender"] for m in M if m["type"] == "honorary" and not m["subnational"])
posts = defaultdict(set)
for m in M:
    if m["subnational"] or GRP[m["type"]] in ("honorary", "office"):
        continue
    posts[m["sender"]].add((m["receiver"], m["city"]))
for w in UNL:
    posts[w["sender"]].add((w["receiver"], "?" + w["qid"]))
# diplomatic city: the city with most embassy-level missions to the state
dcity = {}
for c in ST:
    cc = Counter(m["city"] for m in M if m["receiver"] == c and GRP[m["type"]] == "resident" and not m["subnational"] and m["city"])
    if cc:
        dcity[c] = cc.most_common(1)[0]
cow_s, cow_h = W["sent05"], W["host05"]
rows = []
for c in STATES:
    a, h = abroad_res[c], hosted_res[c]
    cs, ch = cow_s.get(c), cow_h.get(c)
    rs = a / cs if cs else None; rh = h / ch if ch else None
    def flag(r):
        if r is None: return "no 2005 benchmark"
        return "good" if r >= 0.8 else "partial" if r >= 0.5 else "thin"
    osm_s = sum(1 for (x, y) in osm_res if x == c); wd_s = sum(1 for (x, y) in wd_res if x == c)
    rows.append({"code": c, "name": S[c]["name"], "population": S[c]["pop"], "embassies_abroad": a, "embassies_hosted": h,
                 "missions_abroad_all": abroad_all[c], "missions_hosted_all": hosted_all[c], "honorary_abroad": honor[c], "posts": len(posts[c]),
                 "abroad_osm": osm_s, "abroad_wikidata": wd_s, "cow2005_abroad": cs, "cow2005_hosted": ch,
                 "ratio_abroad": round(rs, 2) if rs else None, "ratio_hosted": round(rh, 2) if rh else None,
                 "coverage_abroad": flag(rs), "coverage_hosted": flag(rh),
                 "diplomatic_city": dcity[c][0] if c in dcity else "", "diplomatic_city_n": dcity[c][1] if c in dcity else 0})
CS = pd.DataFrame(rows)
def note(r):
    bits = []
    if r.coverage_abroad == "thin": bits.append(f"its network abroad looks incomplete ({r.embassies_abroad} embassy-level pairs against {r.cow2005_abroad} states hosting its representatives in 2005)")
    if r.coverage_hosted == "thin": bits.append(f"embassies hosted look incomplete ({r.embassies_hosted} against {r.cow2005_hosted} represented there in 2005)")
    if r.abroad_osm and r.abroad_wikidata and r.abroad_wikidata > 1.5 * r.abroad_osm: bits.append("Wikidata lists many more of its embassies than OpenStreetMap maps")
    return "; ".join(bits)
CS["coverage_note"] = CS.apply(note, axis=1)
tw = CS.code == "TW"     # Taiwan's 2005 benchmark counts states that have since switched recognition, so it is not comparable
CS.loc[tw, ["coverage_abroad", "coverage_hosted"]] = "no 2005 benchmark"
CS.loc[tw, "coverage_note"] = "the 2005 benchmark is not comparable: several states have switched recognition since"
CS.to_csv(f"{DATA}/country_summary.csv", index=False)
ok = CS[CS.cow2005_abroad.notna()]
R["coverage"] = {"benchmarked": int(len(ok)), "abroad_good": int((ok.coverage_abroad == "good").sum()), "abroad_partial": int((ok.coverage_abroad == "partial").sum()),
                 "abroad_thin": int((ok.coverage_abroad == "thin").sum()),
                 "hosted_good": int((CS.coverage_hosted == "good").sum()), "hosted_partial": int((CS.coverage_hosted == "partial").sum()), "hosted_thin": int((CS.coverage_hosted == "thin").sum()),
                 "median_ratio_abroad": round(float(ok.ratio_abroad.median()), 2), "median_ratio_hosted": round(float(CS.ratio_hosted.dropna().median()), 2),
                 "thin_abroad_list": ok[ok.coverage_abroad == "thin"].sort_values("cow2005_abroad", ascending=False).name.tolist()[:12],
                 "thin_hosted_list": CS[CS.coverage_hosted == "thin"].sort_values("cow2005_hosted", ascending=False).name.tolist()[:12],
                 "lowy": [{"code": k, "name": S[k]["name"], "lowy": v, "here": len(posts[k]), "pct": round(100 * len(posts[k]) / v)} for k, v in LOWY.items()]}
R["coverage"]["lowy_min_pct"] = min(x["pct"] for x in R["coverage"]["lowy"]); R["coverage"]["lowy_max_pct"] = max(x["pct"] for x in R["coverage"]["lowy"])

# ---------------- rankings ----------------
def top(counter, n=12, only=ST):
    return [{"code": c, "name": cname(c), "n": v} for c, v in counter.most_common() if c in only][:n]
R["networks"] = {"embassies": top(abroad_res, 15), "posts": top(Counter({k: len(v) for k, v in posts.items()}), 15),
                 "honorary": top(honor, 10), "eu_delegations": abroad_res.get("EU", 0) + sum(1 for (a, b) in res_pairs if a == "EU"),
                 "hosted": top(hosted_res, 15)}
R["networks"]["eu_delegations"] = sum(1 for (a, b) in res_pairs if a == "EU")
cities = Counter((m["host"], m["city"]) for m in M if GRP[m["type"]] == "resident" and m["receiver"] == m["host"] and not m["subnational"] and m["sender"] in S)
R["cities"] = [{"city": c, "host": h, "country": cname(h), "n": v} for (h, c), v in cities.most_common(20)]
cons = Counter((m["host"], m["city"]) for m in M if GRP[m["type"]] == "consular" and not m["subnational"])
R["consular_cities"] = [{"city": c, "host": h, "country": cname(h), "n": v} for (h, c), v in cons.most_common(12)]
allc = Counter((m["host"], m["city"]) for m in M if GRP[m["type"]] != "office")
R["all_cities"] = [{"city": c, "host": h, "country": cname(h), "n": v} for (h, c), v in allc.most_common(12)]

# smallest states with embassies abroad
small = sorted([c for c in ST if abroad_res[c] > 0], key=lambda c: S[c]["pop"])[:10]
R["smallest"] = [{"code": c, "name": S[c]["name"], "pop": S[c]["pop"], "n": abroad_res[c], "where": sorted(cname(b) for (a, b) in uni if a == c)[:8]} for c in small]
R["no_embassy_abroad"] = sorted(S[c]["name"] for c in ST if abroad_res[c] == 0)
R["fewest_hosted"] = [{"code": c, "name": S[c]["name"], "n": hosted_res[c]} for c in sorted(ST, key=lambda c: (hosted_res[c], S[c]["pop"]))[:10]]

# ---------------- capitals and seats ----------------
def near_city(rec_filter, lat, lon, km):
    return [m for m in M if rec_filter(m) and gc_km(lat, lon, m["lat"], m["lon"]) < km]
def emb_to(c):
    return lambda m: m["receiver"] == c and GRP[m["type"]] == "resident" and not m["subnational"]
seats = []
for c, off in OFF.items():
    cc = Counter(m["city"] for m in M if emb_to(c)(m))
    tot = sum(cc.values())
    if not tot:
        continue
    top1 = cc.most_common(1)[0]
    seats.append({"code": c, "name": S[c]["name"], "official": off, "n_official": cc.get(off, 0) + (cc.get("Washington, D.C.", 0) if off == "Washington" else 0) + (cc.get("Brasília", 0) if off == "Brasilia" else 0),
                  "top_city": top1[0], "n_top": top1[1], "total": tot, "others": cc.most_common(4)})
R["seats"] = seats
mismatch = [s for s in seats if s["n_top"] > s["n_official"]]
R["seats_mismatch"] = [{"name": s["name"], "official": s["official"], "n_official": s["n_official"], "top_city": s["top_city"], "n_top": s["n_top"], "total": s["total"]} for s in mismatch]
# Israel and Palestine, as recorded
TLV = (32.08, 34.78); JER = (31.778, 35.225); RAM = (31.90, 35.20)
il = [m for m in M if emb_to("IL")(m)]
R["israel"] = {"embassies": len(il), "tel_aviv_area": sum(1 for m in il if gc_km(*TLV, m["lat"], m["lon"]) < 25),
               "jerusalem": sum(1 for m in il if gc_km(*JER, m["lat"], m["lon"]) < 12),
               "jerusalem_senders": sorted(cname(m["sender"]) for m in il if gc_km(*JER, m["lat"], m["lon"]) < 12),
               "other": sum(1 for m in il if gc_km(*TLV, m["lat"], m["lon"]) >= 25 and gc_km(*JER, m["lat"], m["lon"]) >= 12)}
jer_cons = [m for m in M if gc_km(*JER, m["lat"], m["lon"]) < 12 and GRP[m["type"]] == "consular" and not m["subnational"]]
ps = [m for m in M if m["receiver"] == "PS" and GRP[m["type"]] in ("resident", "liaison", "consular") and not m["subnational"]]
R["palestine"] = {"missions_to": len(ps), "ramallah_area": sum(1 for m in ps if gc_km(*RAM, m["lat"], m["lon"]) < 12),
                  "jerusalem": sum(1 for m in ps if gc_km(*JER, m["lat"], m["lon"]) < 12),
                  "jerusalem_consulates": len(jer_cons), "jerusalem_consulate_senders": sorted({cname(m["sender"]) for m in jer_cons}),
                  "palestine_abroad": abroad_res["PS"], "states_with_embassy_level_to_ps": sum(1 for (a, b) in uni if b == "PS"),
                  "by_type": dict(Counter(m["type"] for m in ps))}
# Switzerland: Bern and Geneva
BERN, GVA = (46.948, 7.447), (46.204, 6.143)
ch = [m for m in M if emb_to("CH")(m)]
gva = [m for m in M if gc_km(*GVA, m["lat"], m["lon"]) < 15 and not m["subnational"]]
R["switzerland"] = {"embassies": len(ch), "bern": sum(1 for m in ch if gc_km(*BERN, m["lat"], m["lon"]) < 15),
                    "geneva_perm_missions": sum(1 for m in gva if m["type"] == "perm_mission"), "geneva_all": len(gva),
                    "geneva_embassies_to_ch": sum(1 for m in ch if gc_km(*GVA, m["lat"], m["lon"]) < 15),
                    "perm_missions_un_total": sum(1 for m in M if m["type"] == "perm_mission" and m["receiver"] == "UN")}
NYC = (40.75, -73.97)
R["switzerland"]["new_york_perm_missions"] = sum(1 for m in M if m["type"] == "perm_mission" and gc_km(*NYC, m["lat"], m["lon"]) < 20)
BXL = (50.846, 4.352)
R["brussels"] = {"perm_missions_eu": sum(1 for m in M if m["type"] == "perm_mission" and m["receiver"] == "EU"),
                 "embassies_to_be": sum(1 for m in M if emb_to("BE")(m)), "all_missions": sum(1 for m in M if gc_km(*BXL, m["lat"], m["lon"]) < 15 and not m["subnational"]),
                 "subnational": sum(1 for m in M if gc_km(*BXL, m["lat"], m["lon"]) < 15 and m["subnational"])}
# moved capitals: where embassies and consulates are now
def split(c, a, b, ka=25, kb=25):
    A, B = places_by(a), places_by(b)
    em = [m for m in M if emb_to(c)(m)]
    co = [m for m in M if m["host"] == c and GRP[m["type"]] == "consular" and not m["subnational"]]
    return {"country": S[c]["name"], "new": a, "old": b, "emb_new": sum(1 for m in em if gc_km(*A, m["lat"], m["lon"]) < ka),
            "emb_old": sum(1 for m in em if gc_km(*B, m["lat"], m["lon"]) < kb), "cons_new": sum(1 for m in co if gc_km(*A, m["lat"], m["lon"]) < ka),
            "cons_old": sum(1 for m in co if gc_km(*B, m["lat"], m["lon"]) < kb), "embassies": len(em)}
PLC = {"Abuja": (9.07, 7.49), "Lagos": (6.50, 3.38), "Brasilia": (-15.79, -47.88), "Rio de Janeiro": (-22.91, -43.20), "Sao Paulo": (-23.55, -46.64),
       "Ankara": (39.92, 32.85), "Istanbul": (41.04, 28.99), "Astana": (51.16, 71.45), "Almaty": (43.24, 76.92), "Naypyidaw": (19.75, 96.12),
       "Yangon": (16.80, 96.15), "Dodoma": (-6.17, 35.74), "Dar es Salaam": (-6.80, 39.28), "Yamoussoukro": (6.82, -5.28), "Abidjan": (5.33, -4.03),
       "Islamabad": (33.70, 73.08), "Karachi": (24.86, 67.04), "Canberra": (-35.30, 149.12), "Sydney": (-33.87, 151.21), "Ottawa": (45.42, -75.69),
       "Toronto": (43.67, -79.39), "Sucre": (-19.04, -65.26), "La Paz": (-16.50, -68.13), "Amsterdam": (52.37, 4.89), "The Hague": (52.08, 4.30),
       "Riyadh": (24.70, 46.68), "Jeddah": (21.54, 39.17), "Washington": (38.91, -77.04), "New York": (40.75, -73.97), "Beijing": (39.93, 116.43),
       "Shanghai": (31.22, 121.46), "Gitega": (-3.43, 29.92), "Bujumbura": (-3.38, 29.36), "Porto-Novo": (6.50, 2.62), "Cotonou": (6.37, 2.42)}
places_by = lambda n: PLC[n]
R["moves"] = {k: split(*v) for k, v in {"nigeria": ("NG", "Abuja", "Lagos"), "brazil": ("BR", "Brasilia", "Rio de Janeiro"), "turkey": ("TR", "Ankara", "Istanbul"),
              "kazakhstan": ("KZ", "Astana", "Almaty"), "myanmar": ("MM", "Naypyidaw", "Yangon"), "tanzania": ("TZ", "Dodoma", "Dar es Salaam"),
              "ivory_coast": ("CI", "Yamoussoukro", "Abidjan"), "pakistan": ("PK", "Islamabad", "Karachi"), "bolivia": ("BO", "Sucre", "La Paz"),
              "netherlands": ("NL", "Amsterdam", "The Hague"), "saudi": ("SA", "Riyadh", "Jeddah"), "burundi": ("BI", "Gitega", "Bujumbura"),
              "benin": ("BJ", "Porto-Novo", "Cotonou"), "australia": ("AU", "Canberra", "Sydney")}.items()}
R["moves"]["brazil_sp"] = split("BR", "Brasilia", "Sao Paulo"); R["moves"]["usa_ny"] = split("US", "Washington", "New York", 25, 20)

# ---------------- special cases ----------------
va = [m for m in M if m["sender"] == "VA"]
nun_hosts = {m["receiver"] for m in va if m["type"] == "nunciature"} | {w["receiver"] for w in UNL if w["sender"] == "VA"}
to_va = [m for m in M if m["receiver"] == "VA" and GRP[m["type"]] == "resident"]
R["holy_see"] = {"nunciatures_located": sum(1 for m in va if m["type"] == "nunciature"), "nunciature_hosts": len(nun_hosts & ST),
                 "embassies_to": len(to_va), "embassies_to_in_rome": sum(1 for m in to_va if gc_km(41.90, 12.48, m["lat"], m["lon"]) < 25),
                 "embassies_to_holy_see_pairs": sum(1 for (a, b) in uni if b == "VA"), "abroad_rank": None,
                 "un_without_nunciature_located": sorted(S[c]["name"] for c in UN193 if c not in nun_hosts)[:60]}
rk = [c for c, v in abroad_res.most_common() if c in ST]
R["holy_see"]["abroad_rank"] = rk.index("VA") + 1 if "VA" in rk else None
R["holy_see"]["abroad"] = abroad_res["VA"]
tw = [m for m in M if m["sender"] == "TW" and not m["subnational"]]
tw_emb_hosts = sorted({cname(m["receiver"]) for m in tw if GRP[m["type"]] == "resident"} | {cname(w["receiver"]) for w in UNL if w["sender"] == "TW" and GRP[w["type"]] == "resident"})
to_tw = [m for m in M if m["receiver"] == "TW" and not m["subnational"]]
R["taiwan"] = {"missions": len(tw), "by_type": dict(Counter(m["type"] for m in tw)), "embassy_hosts": tw_emb_hosts, "n_embassy_hosts": len(tw_emb_hosts),
               "liaison_hosts": len({m["receiver"] for m in tw if m["type"] in ("liaison", "embassy_office")} | {w["receiver"] for w in UNL if w["sender"] == "TW" and w["type"] == "liaison"}),
               "to_taiwan": len(to_tw), "to_taiwan_embassy_level": sorted({cname(m["sender"]) for m in to_tw if GRP[m["type"]] == "resident"}),
               "to_taiwan_liaison": sum(1 for m in to_tw if m["type"] in ("liaison", "embassy_office", "delegation")),
               "lowy": LOWY["TW"], "posts": len(posts["TW"])}
xk = [m for m in M if emb_to("XK")(m)]
R["kosovo"] = {"embassies_hosted": len(xk), "senders": sorted({cname(m["sender"]) for m in xk}), "abroad": abroad_res["XK"],
               "liaison_hosted": sum(1 for m in M if m["receiver"] == "XK" and m["type"] in ("liaison", "embassy_office"))}
# Western Sahara: Natural Earth's default borders follow the line of control and put Laayoune and Dakhla inside Morocco, so
# missions in the territory are counted by distance from its two cities instead.
LAA, DAK = (27.15, -13.20), (23.70, -15.94)
ws = [m for m in M if (gc_km(*LAA, m["lat"], m["lon"]) < 25 or gc_km(*DAK, m["lat"], m["lon"]) < 25) and not m["subnational"]]
R["western_sahara"] = {"missions_in_territory": len(ws), "by_type": dict(Counter(m["type"] for m in ws)), "cities": dict(Counter(m["city"] for m in ws)),
                       "senders": sorted({cname(m["sender"]) for m in ws}), "n_senders": len({m["sender"] for m in ws}),
                       "sadr_abroad": abroad_res["EH"], "sadr_hosts": sorted(cname(b) for (a, b) in uni if a == "EH"),
                       "years": sorted(m["wd_year"] for m in ws if m.get("wd_year"))}
R["eu"] = {"delegations": R["networks"]["eu_delegations"], "located": sum(1 for m in M if m["sender"] == "EU")}
R["order_of_malta"] = {"missions": sum(1 for m in M if m["sender"] == "XO"), "pairs": sum(1 for (a, b) in res_pairs if a == "XO")}

# ---------------- neighbours without embassies ----------------
geo = defaultdict(list)
for u in units:
    if u["state"] in ST and (u["iso"] == u["state"] or u["a3"] in ("PSX", "SAH", "KOS", "TWN")):
        geo[u["state"]].append(u["geom"])
geo = {k: unary_union(v).buffer(0.02) for k, v in geo.items()}
nb = []
keys = sorted(geo)
from shapely.strtree import STRtree
tr = STRtree([geo[k] for k in keys])
for i, a in enumerate(keys):
    for j in tr.query(geo[a], predicate="intersects"):
        b = keys[j]
        if b <= a:
            continue
        nb.append((a, b))
nopair = []
for a, b in nb:
    if (a, b) in uni or (b, a) in uni:
        continue
    anyl = [lvl for lvl in (level(pair[(a, b)]) if (a, b) in pair else None, level(pair[(b, a)]) if (b, a) in pair else None) if lvl]
    d = float(gc_km(S[a]["capital"]["lat"], S[a]["capital"]["lon"], S[b]["capital"]["lat"], S[b]["capital"]["lon"]))
    cow = int((a, b) in W["rep05"]) + int((b, a) in W["rep05"])
    nopair.append({"a": S[a]["name"], "b": S[b]["name"], "codes": [a, b], "km": round(d), "other_links": anyl, "cow2005_directions": cow,
                   "coverage": [CS.set_index("code").loc[a, "coverage_hosted"], CS.set_index("code").loc[b, "coverage_hosted"]]})
nopair.sort(key=lambda x: x["km"])
R["neighbours"] = {"pairs": len(nb), "without_embassy": len(nopair), "list": nopair,
                   "both_ways": sum(1 for a, b in nb if (a, b) in uni and (b, a) in uni)}

# ---------------- clusters ----------------
resm = [m for m in M if GRP[m["type"]] in ("resident", "multilateral") and not m["subnational"]]
la = np.array([m["lat"] for m in resm]); lo = np.array([m["lon"] for m in resm])
cnt = np.array([int((gc_km(la[i], lo[i], la, lo) < 1.0).sum()) for i in range(len(resm))])
order = np.argsort(-cnt); used = np.zeros(len(resm), bool); cl = []
for i in order:
    if used[i]:
        continue
    near = gc_km(la[i], lo[i], la, lo) < 1.0
    cl.append({"city": resm[i]["city"], "country": cname(resm[i]["host"]), "n": int(cnt[i]), "lat": round(float(la[i]), 4), "lon": round(float(lo[i]), 4)})
    used |= gc_km(la[i], lo[i], la, lo) < 3.0
    if len(cl) >= 15:
        break
R["clusters"] = cl

# ---------------- odd pairs ----------------
odd = []
for (a, b) in uni:
    if a in ("VA",) or b in ("VA",):
        continue
    pa, pb = S[a]["pop"], S[b]["pop"]
    d = float(gc_km(S[a]["capital"]["lat"], S[a]["capital"]["lon"], S[b]["capital"]["lat"], S[b]["capital"]["lon"]))
    if pa < 12e6 and pb < 12e6 and d > 9000:
        odd.append({"sender": S[a]["name"], "receiver": S[b]["name"], "km": round(d), "pops": [pa, pb],
                    "city": next(iter(sorted(c for c in pair[(a, b)]["cities"] if c)), "")})
odd.sort(key=lambda x: -x["km"])
R["odd_pairs"] = {"n": len(odd), "list": odd[:20]}
far = []
for (a, b) in uni:
    d = float(gc_km(S[a]["capital"]["lat"], S[a]["capital"]["lon"], S[b]["capital"]["lat"], S[b]["capital"]["lon"]))
    far.append((d, a, b))
far.sort(reverse=True)
R["longest"] = [{"sender": S[a]["name"], "receiver": S[b]["name"], "km": round(d)} for d, a, b in far[:8]]

# ---------------- Wikidata opening years ----------------
yrs = [m["wd_year"] for m in M if m.get("wd_year") and GRP[m["type"]] == "resident" and 1700 <= m["wd_year"] <= 2026]
R["opening_years"] = {"n": len(yrs), "median": int(np.median(yrs)) if yrs else None, "since_2000": sum(1 for y in yrs if y >= 2000),
                      "hist": {str(d): sum(1 for y in yrs if d <= y < d + 10) for d in range(1900, 2030, 10)},
                      "before_1900": sum(1 for y in yrs if y < 1900)}

# ---------------- COW ----------------
ser = {s["year"]: s for s in W["series"]}
R["cow"] = {"years": W["years"], "first": W["years"][0], "last": W["years"][-1], "codes": W["n_codes"], "pairs_ever": W["n_pairs"],
            "series": W["series"], "splits": W["splits"], "new": W["new"], "net": W["net"],
            "states_1817": ser[1817]["states"], "states_2005": ser[2005]["states"], "rep_1817": ser[1817]["rep"], "rep_2005": ser[2005]["rep"],
            "rep_1980": ser[1980]["rep"], "density_1817": ser[1817]["density"], "density_2005": ser[2005]["density"],
            "amb_share_1914": ser[1914]["amb_share"], "amb_share_2005": ser[2005]["amb_share"], "amb_share_1970": ser[1970]["amb_share"],
            "amb_1914": ser[1914]["amb"], "amb_1817": ser[1817]["amb"], "amb_2005": ser[2005]["amb"],
            "new_1960s": sum(n["n"] for n in W["new"] if n["year"] in (1960, 1965)), "new_1920": next(n["n"] for n in W["new"] if n["year"] == 1920),
            "new_1995": next(n["n"] for n in W["new"] if n["year"] == 1995), "peak_rep_year": max(W["series"], key=lambda s: s["rep"])["year"],
            "peak_rep": max(s["rep"] for s in W["series"])}
spl = {k: {r["year"]: r for r in v} for k, v in W["splits"].items()}
R["cow"]["us_1950"], R["cow"]["ussr_1950"] = spl["us_ussr"][1950]["a"], spl["us_ussr"][1950]["b"]
R["cow"]["us_1985"], R["cow"]["ussr_1985"] = spl["us_ussr"][1985]["a"], spl["us_ussr"][1985]["b"]
R["cow"]["ussr_only_1985"], R["cow"]["us_only_1985"] = spl["us_ussr"][1985]["b_only"], spl["us_ussr"][1985]["a_only"]
R["cow"]["prc_1950"], R["cow"]["roc_1950"] = spl["prc_roc"][1950]["a"], spl["prc_roc"][1950]["b"]
R["cow"]["prc_1970"], R["cow"]["roc_1970"] = spl["prc_roc"][1970]["a"], spl["prc_roc"][1970]["b"]
R["cow"]["prc_1975"], R["cow"]["roc_1975"] = spl["prc_roc"][1975]["a"], spl["prc_roc"][1975]["b"]
R["cow"]["prc_2005"], R["cow"]["roc_2005"] = spl["prc_roc"][2005]["a"], spl["prc_roc"][2005]["b"]
R["cow"]["prc_roc_both_max"] = max(r["both"] for r in W["splits"]["prc_roc"])
R["cow"]["frg_1965"], R["cow"]["gdr_1965"] = spl["frg_gdr"][1965]["a"], spl["frg_gdr"][1965]["b"]
R["cow"]["frg_1975"], R["cow"]["gdr_1975"] = spl["frg_gdr"][1975]["a"], spl["frg_gdr"][1975]["b"]
R["cow"]["frg_1985"], R["cow"]["gdr_1985"] = spl["frg_gdr"][1985]["a"], spl["frg_gdr"][1985]["b"]
R["cow"]["gdr_both_1985"] = spl["frg_gdr"][1985]["both"]

R["countries"] = {"states": len(ST), "un": len(UN193)}
R["seats_mismatch_n"] = len(R["seats_mismatch"])
R["deep"] = pickle.load(open(f"{WORK}/deep.pkl", "rb"))
R["params"] = {"merge_m": 350, "odd_pop_m": 12, "odd_km": 9000, "cluster_km": 1, "lowy_countries": 66, "waves": len(W["years"])}
R["data"]["flagged"] = len(G["flagged"]); R["data"]["hand_corrections"] = LOG.get("hand_corrections", 0)
R["data"]["flagged_states"] = sorted({cname(x["receiver"] if x["sender"] == "TW" else x["sender"]) for x in G["flagged"]})
R["taiwan"]["allies_n"] = 12
R["cow"]["amb_share_1817"] = ser[1817]["amb_share"]
R["cow"]["rep_1985"] = ser[1985]["rep"]
R["cow"]["mutual_2005"] = ser[2005]["mutual_rep_pairs"]
R["cow"]["mutual_1817"] = ser[1817]["mutual_rep_pairs"]
R["cow"]["rep_1914"] = ser[1914]["rep"]
R["cow"]["states_1914"] = ser[1914]["states"]; R["cow"]["states_1950"] = ser[1950]["states"]; R["cow"]["states_1975"] = ser[1975]["states"]
R["cow"]["top_host_1817"] = W["net"]["1817"]["hosts"][0]; R["cow"]["top_host_2005"] = W["net"]["2005"]["hosts"][0]
R["cow"]["top_sender_2005"] = W["net"]["2005"]["senders"][0]
jsave(R, f"{DATA}/results.json", indent=1)
pickle.dump({"CS": CS, "pair": {k: {"types": dict(v["types"]), "cities": sorted(c for c in v["cities"] if c), "unloc": v["wd_unloc"]} for k, v in pair.items()},
             "uni": uni, "dcity": dcity, "posts": {k: len(v) for k, v in posts.items()}}, open(f"{WORK}/res.pkl", "wb"))
p = lambda *a: print(*a)
p("data", {k: v for k, v in R["data"].items() if k != "wd_classes"})
p("pairs", R["pairs"]); p("coverage", {k: v for k, v in R["coverage"].items()})
p("networks", [(x["name"], x["n"]) for x in R["networks"]["embassies"]]); p("posts", [(x["name"], x["n"]) for x in R["networks"]["posts"]])
p("hosted", [(x["name"], x["n"]) for x in R["networks"]["hosted"]]); p("honorary", [(x["name"], x["n"]) for x in R["networks"]["honorary"]])
p("cities", [(x["city"], x["n"]) for x in R["cities"]]); p("consular", [(x["city"], x["n"]) for x in R["consular_cities"]])
p("smallest", [(x["name"], x["pop"], x["n"]) for x in R["smallest"]]); p("no embassy abroad", R["no_embassy_abroad"]); p("fewest hosted", R["fewest_hosted"])
p("seats mismatch", R["seats_mismatch"]); p("israel", R["israel"]); p("palestine", R["palestine"]); p("swiss", R["switzerland"]); p("brussels", R["brussels"])
p("moves", {k: (v["emb_new"], v["emb_old"], v["cons_new"], v["cons_old"], v["embassies"]) for k, v in R["moves"].items()})
p("holy see", {k: v for k, v in R["holy_see"].items() if k != "un_without_nunciature_located"}, R["holy_see"]["un_without_nunciature_located"])
p("taiwan", R["taiwan"]); p("kosovo", R["kosovo"]); p("ws", R["western_sahara"]); p("eu", R["eu"], R["order_of_malta"])
p("neighbours", R["neighbours"]["pairs"], R["neighbours"]["without_embassy"], [(x["a"], x["b"], x["km"], x["other_links"], x["cow2005_directions"], x["coverage"]) for x in R["neighbours"]["list"][:25]])
p("clusters", [(c["city"], c["n"]) for c in R["clusters"]]); p("odd", R["odd_pairs"]["n"], R["odd_pairs"]["list"][:10]); p("longest", R["longest"][:4])
p("opening", R["opening_years"])
