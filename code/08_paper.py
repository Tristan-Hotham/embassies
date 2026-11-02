"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/Hotham_Embassies.pdf and .tex (figures f_*.png beside them). The DOI stays a 10.5281/zenodo.23899269 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Embassies"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if v is None: return "none"
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f2": return f"{float(v):.2f}"
    if f in ("yr", "ord"): return fmt(v, f)
    return tex(str(v))


TL = ("\\begin{table}[tbp]\\centering\\small\\caption{Posts (all missions except honorary consulates, by city) against the Lowy Institute Global Diplomacy Index 2024, and the largest embassy-level networks.}\\label{tab:lowy}"
      "\\begin{tabular}{lrrr@{\\hspace{2.2em}}lr}\\toprule Country & Lowy & Here & Share & Embassy-level network & States\\\\\\midrule\n")
rows = R["coverage"]["lowy"]; net = R["networks"]["embassies"][:10]
for k in range(max(len(rows), len(net))):
    a = rows[k] if k < len(rows) else None; b = net[k] if k < len(net) else None
    TL += (f"{tex(a['name'])} & {a['lowy']} & {a['here']} & {a['pct']}\\% & " if a else " & & & & ") + (f"{tex(b['name'])} & {b['n']}\\\\\n" if b else " & \\\\\n")
TL += "\\bottomrule\\end{tabular}\\end{table}"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{States whose official capital is not where most embassies to them are (embassy-level missions in each city).}\\label{tab:seats}"
      "\\begin{tabular}{llrlr}\\toprule State & Official capital & Embassies & Embassy city & Embassies\\\\\\midrule\n" +
      "".join(f"{tex(s['name'])} & {tex(s['official'])} & {s['n_official']} & {tex(s['top_city'])} & {s['n_top']}\\\\\n" for s in R["seats_mismatch"]) +
      "\\bottomrule\\end{tabular}\\end{table}")
D = jload(f"{DATA}/deep_history.json")["entries"]
seen, TD = set(), ("{\\small\\begin{longtable}{p{1.6cm}p{4.5cm}p{3.7cm}p{3.6cm}c}\\caption{The deep-history sample: one row per event (congresses and letter networks draw several lines). Sources are English Wikipedia articles. Status: C confirmed (year in the article), A approximate (nearby year), N not confirmed.}\\label{tab:deep}\\\\\\toprule Year & Event & Between & Source article & Status\\\\\\midrule\\endfirsthead\\toprule Year & Event & Between & Source article & Status\\\\\\midrule\\endhead\n")
for e in D:
    k = (e["year"], e["title"])
    if k in seen:
        continue
    seen.add(k)
    pair = [x for x in D if (x["year"], x["title"]) == k]
    ends = sorted({x["from"] for x in pair} | {x["to"] for x in pair}) if len(pair) > 1 else [e["from"], e["to"]]
    TD += f"{('c. ' if e['approx'] else '') + fmt(e['year'], 'yr')} & {tex(e['title'])} & {tex(', '.join(ends) if len(pair) > 1 else e['from'] + ' to ' + e['to'])} & {tex(e['source'].replace('Wikipedia: ', ''))} & {', '.join(sorted({ {'confirmed': 'C', 'approximate': 'A'}.get(x['st'], 'N') for x in pair}))}\\\\\n"
TD += "\\bottomrule\\end{longtable}}"
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|DOI_LINK)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("LOWY", TL), ("SEATS", TS), ("DEEP", TD)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("{{DOI_LINK}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
