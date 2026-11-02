"""Deep history frames for the timeline: data/deep_history.json from code/deep_history.py and data/deep_history.csv.

data/deep_history.csv is authoritative for each line's source article and checking status: the dates were checked
against the cited Wikipedia articles in a browser and the CSV updated (status and five corrected source titles). This
script reads those columns and never overwrites the CSV; it writes the CSV only if it does not exist yet."""
import csv, pickle
import pandas as pd
from collections import Counter
from common import *
from deep_history import C, E, STATUS

rows = []
for k, (y, ap, a, b, kind, title, note, art) in enumerate(E):
    assert a in C and b in C, (a, b)
    rows.append({"id": k, "year": y, "approx": ap, "from": a, "to": b, "lat1": C[a][0], "lon1": C[a][1], "lat2": C[b][0], "lon2": C[b][1],
                 "kind": kind, "title": title, "note": note, "source": "Wikipedia: " + art, "status": STATUS})
CSV = f"{DATA}/deep_history.csv"
if os.path.exists(CSV):
    chk = pd.read_csv(CSV).set_index("id")
    for r in rows:
        c = chk.loc[r["id"]]
        assert int(c.year) == r["year"] and c.title == r["title"], (r["id"], c.year, c.title)     # same line
        r["source"], r["status"] = c.source, c.status
else:
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows:
    r["st"] = "confirmed" if r["status"].startswith("confirmed") else "approximate" if r["status"].startswith("approximate") else "not confirmed"
jsave({"entries": rows}, f"{DATA}/deep_history.json")
events = sorted({(r["year"], r["title"]) for r in rows})
D = {"entries": len(rows), "events": len(events), "first_year": min(r["year"] for r in rows), "last_year": max(r["year"] for r in rows),
     "confirmed": sum(r["st"] == "confirmed" for r in rows), "approximate": sum(r["st"] == "approximate" for r in rows),
     "not_confirmed": sum(r["st"] == "not confirmed" for r in rows), "courts": len({r["from"] for r in rows} | {r["to"] for r in rows}), "by_kind": dict(Counter(r["kind"] for r in rows)),
     "first_resident": min(r["year"] for r in rows if r["kind"] == "resident"), "amarna": sum(1 for r in rows if r["title"].startswith("Amarna")),
     "bc": sum(1 for r in rows if r["year"] < 0), "ottoman_first": next(r["year"] for r in rows if r["title"] == "First permanent Ottoman embassy"),
     "spain_london": next(r["year"] for r in rows if r["title"].startswith("Spain's resident")), "articles": len({r["source"] for r in rows})}
pickle.dump(D, open(f"{WORK}/deep.pkl", "wb"))
print(D)
