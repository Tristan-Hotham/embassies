"""The diplomatic web from 1817 to 2005, from the Correlates of War Diplomatic Exchange data (Bayer 2006).

Each row of the raw file is a directed pair: DR_at_1 is the level at which state 2 is represented in state 1
(0 none, 1 charge d'affaires, 2 minister, 3 ambassador, 9 other). Every pair appears in both orders and the two
codings agree (checked). Level 9 is rare in most years, but in 1950, 1955, 1960 and 1965 every represented pair carries
it: the level was not recorded for those years. So representation counts levels 1, 2, 3 and 9, and ambassador-level
counts are left empty for the years without levels. COW codes are named from the COW state list and placed at a
capital (with a few dated moves: St Petersburg to Moscow, Constantinople to Ankara, Rio to Brasilia, Lagos to Abuja,
Karachi to Islamabad, Melbourne to Canberra, Almaty to Astana, Jeddah to Riyadh for embassies, Bonn for West Germany).
Outputs: data/cow_timeline.json (page), WORK/cow.pkl (results)."""
import io, pickle
import pandas as pd
from common import *

C = pickle.load(open(f"{WORK}/countries.pkl", "rb"))
S = C["S"]
d = pd.read_csv(COW)
st = pd.read_csv(io.StringIO(open(COW_STATES, encoding="utf-8").read().replace("\r", "\n")))
names = st.groupby("ccode").statenme.first().to_dict()
abb = st.groupby("ccode").stateabb.first().to_dict()

# COW code -> modern ISO code (None for states with no single successor)
ISO = {2: "US", 20: "CA", 31: "BS", 40: "CU", 41: "HT", 42: "DO", 51: "JM", 52: "TT", 53: "BB", 54: "DM", 55: "GD", 56: "LC", 57: "VC",
       58: "AG", 60: "KN", 70: "MX", 80: "BZ", 90: "GT", 91: "HN", 92: "SV", 93: "NI", 94: "CR", 95: "PA", 100: "CO", 101: "VE", 110: "GY",
       115: "SR", 130: "EC", 135: "PE", 140: "BR", 145: "BO", 150: "PY", 155: "CL", 160: "AR", 165: "UY", 200: "GB", 205: "IE", 210: "NL",
       211: "BE", 212: "LU", 220: "FR", 221: "MC", 223: "LI", 225: "CH", 230: "ES", 232: "AD", 235: "PT", 255: "DE", 260: "DE",
       290: "PL", 305: "AT", 310: "HU", 316: "CZ", 317: "SK", 325: "IT", 331: "SM", 338: "MT", 339: "AL", 341: "ME", 343: "MK", 344: "HR",
       345: "RS", 346: "BA", 347: "XK", 349: "SI", 350: "GR", 352: "CY", 355: "BG", 359: "MD", 360: "RO", 365: "RU", 366: "EE", 367: "LV",
       368: "LT", 369: "UA", 370: "BY", 371: "AM", 372: "GE", 373: "AZ", 375: "FI", 380: "SE", 385: "NO", 390: "DK", 395: "IS", 402: "CV",
       403: "ST", 404: "GW", 411: "GQ", 420: "GM", 432: "ML", 433: "SN", 434: "BJ", 435: "MR", 436: "NE", 437: "CI", 438: "GN", 439: "BF",
       450: "LR", 451: "SL", 452: "GH", 461: "TG", 471: "CM", 475: "NG", 481: "GA", 482: "CF", 483: "TD", 484: "CG", 490: "CD", 500: "UG",
       501: "KE", 510: "TZ", 516: "BI", 517: "RW", 520: "SO", 522: "DJ", 530: "ET", 531: "ER", 540: "AO", 541: "MZ", 551: "ZM", 552: "ZW",
       553: "MW", 560: "ZA", 565: "NA", 570: "LS", 571: "BW", 572: "SZ", 580: "MG", 581: "KM", 590: "MU", 591: "SC", 600: "MA", 615: "DZ",
       616: "TN", 620: "LY", 625: "SD", 626: "SS", 630: "IR", 640: "TR", 645: "IQ", 651: "EG", 652: "SY", 660: "LB", 663: "JO", 666: "IL",
       670: "SA", 679: "YE", 690: "KW", 692: "BH", 694: "QA", 696: "AE", 698: "OM", 700: "AF", 701: "TM", 702: "TJ", 703: "KG", 704: "UZ",
       705: "KZ", 710: "CN", 712: "MN", 713: "TW", 731: "KP", 732: "KR", 740: "JP", 750: "IN", 760: "BT", 770: "PK", 771: "BD", 775: "MM",
       780: "LK", 781: "MV", 790: "NP", 800: "TH", 811: "KH", 812: "LA", 816: "VN", 820: "MY", 830: "SG", 835: "BN", 840: "PH", 850: "ID",
       860: "TL", 900: "AU", 910: "PG", 920: "NZ", 935: "VU", 940: "SB", 946: "KI", 947: "TV", 950: "FJ", 955: "TO", 970: "NR", 983: "MH",
       986: "PW", 987: "FM", 990: "WS"}
# Historical capitals (lat, lon) for states with no modern successor, and dated moves: (from_year, name, lat, lon)
HIST = {240: [(0, "Hanover", 52.37, 9.73)], 245: [(0, "Munich", 48.14, 11.58)], 267: [(0, "Karlsruhe", 49.01, 8.40)],
        269: [(0, "Dresden", 51.05, 13.74)], 271: [(0, "Stuttgart", 48.78, 9.18)], 273: [(0, "Kassel", 51.31, 9.48)],
        275: [(0, "Darmstadt", 49.87, 8.65)], 280: [(0, "Schwerin", 53.63, 11.41)], 300: [(0, "Vienna", 48.21, 16.37)],
        315: [(0, "Prague", 50.08, 14.44)], 327: [(0, "Rome", 41.90, 12.45)], 329: [(0, "Naples", 40.85, 14.27)],
        332: [(0, "Modena", 44.65, 10.93)], 335: [(0, "Parma", 44.80, 10.33)], 337: [(0, "Florence", 43.77, 11.25)],
        265: [(0, "East Berlin", 52.52, 13.41)], 260: [(0, "Bonn", 50.73, 7.10)], 511: [(0, "Zanzibar", -6.16, 39.19)],
        678: [(0, "Sanaa", 15.35, 44.21)], 680: [(0, "Aden", 12.79, 45.03)], 730: [(0, "Seoul", 37.57, 126.98)],
        817: [(0, "Saigon", 10.78, 106.70)], 711: [(0, "Lhasa", 29.65, 91.10)],
        365: [(0, "St Petersburg", 59.94, 30.31), (1918, "Moscow", 55.76, 37.62)], 640: [(0, "Constantinople", 41.01, 28.98), (1923, "Ankara", 39.93, 32.86)],
        140: [(0, "Rio de Janeiro", -22.91, -43.17), (1960, "Brasilia", -15.79, -47.88)], 475: [(0, "Lagos", 6.45, 3.39), (1991, "Abuja", 9.08, 7.40)],
        770: [(0, "Karachi", 24.86, 67.01), (1967, "Islamabad", 33.69, 73.06)], 900: [(0, "Melbourne", -37.81, 144.96), (1927, "Canberra", -35.28, 149.13)],
        705: [(0, "Almaty", 43.24, 76.89), (1997, "Astana", 51.17, 71.43)], 670: [(0, "Jeddah", 21.49, 39.19), (1984, "Riyadh", 24.71, 46.68)],
        710: [(0, "Beijing", 39.91, 116.39)], 713: [(0, "Taipei", 25.04, 121.56)], 255: [(0, "Berlin", 52.52, 13.40)],
        345: [(0, "Belgrade", 44.82, 20.46)], 553: [(0, "Zomba", -15.39, 35.32), (1975, "Lilongwe", -13.97, 33.79)],
        437: [(0, "Abidjan", 5.35, -4.01)], 510: [(0, "Dar es Salaam", -6.80, 39.28)], 80: [(0, "Belize City", 17.50, -88.20), (1970, "Belmopan", 17.25, -88.77)],
        666: [(0, "Tel Aviv", 32.08, 34.78)], 600: [(0, "Rabat", 34.02, -6.84)], 616: [(0, "Tunis", 36.80, 10.18)]}
NOTE_666 = "Israel is placed at Tel Aviv on the timeline map because that is where most embassies to it were located; this is a drawing position, not a statement about its capital."
codes = sorted(set(d.ccode1) | set(d.ccode2))
STATE = []
for c in codes:
    iso = ISO.get(c)
    if c in HIST:
        caps = [list(x) for x in HIST[c]]
    else:
        assert iso, (c, names.get(c))
        k = S[iso]["capital"]
        caps = [[0, k["name"], round(k["lat"], 3), round(k["lon"], 3)]]
    nm = {255: "Prussia, then Germany", 300: "Austria (Austria-Hungary 1867 to 1918)", 260: "West Germany", 265: "East Germany", 365: "Russia (Soviet Union 1922 to 1991)", 345: "Yugoslavia, then Serbia",
          315: "Czechoslovakia", 816: "Vietnam (North Vietnam to 1976)", 817: "South Vietnam", 678: "North Yemen",
          680: "South Yemen", 730: "Korea", 710: "China (People's Republic from 1949)", 713: "Taiwan (Republic of China)", 640: "Ottoman Empire, then Turkey",
          740: "Japan", 2: "United States", 200: "United Kingdom"}.get(c) or names.get(c, str(c))
    STATE.append({"c": int(c), "abb": abb.get(c, ""), "name": nm, "iso": iso, "caps": caps})
idx = {s["c"]: i for i, s in enumerate(STATE)}
YEARS = sorted(d.year.unique().tolist())
YI = {y: k for k, y in enumerate(YEARS)}

# directed levels: lev[(host, sender)][year] = DR (from DR_at_1 of row host=ccode1, sender=ccode2)
lv = d[["ccode1", "ccode2", "year", "DR_at_1"]].copy()
lv.columns = ["host", "sender", "year", "lev"]
lv["rep"] = lv.lev.isin([1, 2, 3, 9])
lv["amb"] = lv.lev == 3
members = d.groupby("year").apply(lambda g: sorted(set(g.ccode1) | set(g.ccode2))).to_dict()

# per-pair masks for the page
pairs = {}
for r in lv[lv.rep].itertuples(index=False):
    i, j = idx[r.host], idx[r.sender]
    a, b = min(i, j), max(i, j)
    p = pairs.setdefault((a, b), [0, 0, 0, 0])     # rep a<-b (b in a), rep b<-a, amb a<-b, amb b<-a
    k = 0 if i == a else 1
    p[k] |= 1 << YI[r.year]
    if r.amb:
        p[k + 2] |= 1 << YI[r.year]
P = [[a, b] + v for (a, b), v in sorted(pairs.items())]

# series
ser = []
for y in YEARS:
    g = lv[lv.year == y]
    n = len(members[y])
    rep = g[g.rep]; amb = g[g.amb]
    mutual = amb.merge(amb, left_on=["host", "sender"], right_on=["sender", "host"])
    hosted = rep.groupby("host").size()
    sent = rep.groupby("sender").size()
    known = (g.lev == 9).sum() < 0.5 * max(1, len(rep))
    mutual_rep = rep.merge(rep, left_on=["host", "sender"], right_on=["sender", "host"])
    ser.append({"year": int(y), "states": n, "possible": n * (n - 1), "rep": int(len(rep)), "levels": bool(known),
                "amb": int(len(amb)) if known else None, "mutual_amb_pairs": int(len(mutual) // 2) if known else None,
                "mutual_rep_pairs": int(len(mutual_rep) // 2), "density": round(100 * len(rep) / (n * (n - 1)), 1),
                "amb_share": round(100 * len(amb) / max(1, len(rep)), 1) if known else None, "other9": int((g.lev == 9).sum()),
                "states_sending_amb": int(amb.sender.nunique()) if known else None,
                "top_hosts": [[STATE[idx[c]]["name"], int(v)] for c, v in hosted.sort_values(ascending=False).head(5).items()],
                "top_senders": [[STATE[idx[c]]["name"], int(v)] for c, v in sent.sort_values(ascending=False).head(5).items()]})


def present(sender, y, level="rep"):
    g = lv[(lv.year == y) & (lv.sender == sender)]
    return set(g[g[level]].host)


# Cold War and recognition splits: how many states host each side's representation
splits = {}
for nm, a, b, y0, y1 in (("us_ussr", 2, 365, 1950, 2005), ("prc_roc", 710, 713, 1950, 2005), ("frg_gdr", 260, 265, 1955, 1990)):
    rows = []
    for y in YEARS:
        if y < y0 or y > y1:
            continue
        A, B = present(a, y), present(b, y)
        rows.append({"year": int(y), "a": len(A), "b": len(B), "both": len(A & B), "a_only": len(A - B), "b_only": len(B - A),
                     "states": len(members[y])})
    splits[nm] = rows
# newcomers per year (decolonisation waves)
new = []
seen = set()
for y in YEARS:
    m = set(members[y]); add = sorted(m - seen); seen |= m
    if y > YEARS[0]:
        new.append({"year": int(y), "n": len(add), "names": [STATE[idx[c]]["name"] for c in add]})
# biggest networks in 2005 and in 1950, and the 1817 web
net = {}
for y in (1817, 1914, 1950, 1975, 2005):
    g = lv[(lv.year == y) & lv.rep]
    net[str(y)] = {"senders": [[STATE[idx[c]]["name"], int(v)] for c, v in g.groupby("sender").size().sort_values(ascending=False).head(10).items()],
                   "hosts": [[STATE[idx[c]]["name"], int(v)] for c, v in g.groupby("host").size().sort_values(ascending=False).head(10).items()]}
# 2005 network size by ISO code (for the coverage comparison with 2026)
g = lv[(lv.year == 2005) & lv.rep]
sent05 = {ISO[c]: int(v) for c, v in g.groupby("sender").size().items() if ISO.get(c)}
host05 = {ISO[c]: int(v) for c, v in g.groupby("host").size().items() if ISO.get(c)}
amb05 = {(ISO.get(r.sender), ISO.get(r.host)) for r in g[g.amb].itertuples()}
rep05 = {(ISO.get(r.sender), ISO.get(r.host)) for r in g.itertuples()}

tl = {"years": YEARS, "states": STATE, "pairs": P, "series": ser, "splits": splits, "new": new, "note": NOTE_666}
jsave(tl, f"{DATA}/cow_timeline.json")
pickle.dump({"series": ser, "splits": splits, "new": new, "net": net, "sent05": sent05, "host05": host05, "rep05": rep05, "amb05": amb05,
             "n_pairs": len(P), "n_codes": len(codes), "years": YEARS}, open(f"{WORK}/cow.pkl", "wb"))
print("COW:", len(codes), "states,", len(P), "pairs ever represented;", os.path.getsize(f"{DATA}/cow_timeline.json") // 1024, "KB")
for s in ser[::4] + [ser[-1]]:
    print(s["year"], s["states"], s["rep"], s["amb"], s["density"], s["amb_share"], s["other9"], s["top_hosts"][:2])
print({k: v[::3] for k, v in splits.items()})
print([(n["year"], n["n"]) for n in new])
