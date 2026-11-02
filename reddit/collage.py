"""Reddit collage (r/dataisbeautiful style, light background): reddit/every_embassy.png, 2560 x 2880 px.
Run after code/07_figures.py. Every number comes from data/results.json."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import importlib.util
spec = importlib.util.spec_from_file_location("fig", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code", "07_figures.py"))
F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D

R, M, S = F.R, F.M, F.S
BG, FG, MUT, HOT, COOL, GOLD = F.BG, F.FG, F.MUT, F.HOT, F.COOL, F.GOLD
halo = [pe.withStroke(linewidth=4, foreground=BG)]
fig = plt.figure(figsize=(16, 18), dpi=160, facecolor=BG)
fig.text(.04, .963, "Every Embassy in the World", fontproperties=F.DISP, fontsize=46, color=FG, va="top")
fig.text(.04, .918, f"{R['data']['missions']:,} embassies, consulates and other diplomatic missions, mapped from OpenStreetMap and Wikidata",
         fontsize=15, color=FG, va="top")
fig.text(.04, .897, f"{R['pairs']['resident_states']:,} pairs of states with an embassy-level mission ({R['pairs']['density_pc']}% of all possible pairs)",
         fontsize=15, color=MUT, va="top")
ax = fig.add_axes([.02, .45, .96, .43]); ax.set_facecolor(BG); F.draw_land(ax); ax.set_ylim(-56, 80)
for g in ("honorary", "liaison", "multilateral", "consular", "resident"):
    pts = np.array([[m["lon"], m["lat"]] for m in M if F.grp(m) == g and not m["subnational"]])
    ax.scatter(pts[:, 0], pts[:, 1], s=7 if g == "resident" else 5, c=F.GRPCOL[g], lw=0, alpha=.8, zorder=3)
C = {c["city"]: c for c in R["cities"]}
cons = {c["city"]: c for c in R["consular_cities"]}
labs = [  # (text, point lat/lon, label position in open sea)
    (f"Washington, D.C.\n{C['Washington, D.C.']['n']} embassies, the most", (38.9, -77.0), (16, -36)),
    (f"Brussels\n{C['Brussels']['n']} embassies", (50.85, 4.35), (51, -14)),
    (f"Barcelona: {cons['Barcelona']['n']} consulates,\nmore than any other city", (41.39, 2.17), (36, -26)),
    (f"Pretoria\n{C['Pretoria']['n']} embassies", (-25.75, 28.19), (-40, 58)),
    (f"Beijing\n{C['Beijing']['n']} embassies", (39.93, 116.43), (33, 162)),
    (f"Canberra\n{C['Canberra']['n']} embassies", (-35.3, 149.1), (-48, 160)),
    (f"Brasilia\n{C['Brasília']['n']} embassies", (-15.79, -47.88), (-28, -26)),
]
for t, p, q in labs:
    ax.plot([p[1], q[1]], [p[0], q[0]], color=FG, lw=.8, zorder=4)
    ax.scatter([p[1]], [p[0]], s=30, facecolor="none", edgecolor=FG, lw=1.2, zorder=5)
    side = abs(q[0] - p[0]) < 4          # beside the point: text to the left, else below it
    ax.text(q[1] - (1 if side else 0), q[0] - (0 if side else 1), t, fontsize=12.5, color=FG, ha="right" if side else "center",
            va="center" if side else "top", zorder=6, path_effects=halo, fontweight="medium", linespacing=1.1)
names = {"resident": "Embassy, high commission, nunciature", "consular": "Consulate", "honorary": "Honorary consulate",
         "liaison": "Representative office", "multilateral": "Permanent mission"}
ax.legend([Line2D([], [], marker="o", ls="", color=F.GRPCOL[g], ms=9) for g in names], list(names.values()), loc="lower left",
          bbox_to_anchor=(0, -.1), frameon=False, fontsize=12, ncol=3)
# bottom panels
a1 = fig.add_axes([.17, .1, .3, .3]); rows = R["networks"]["embassies"][:12][::-1]
a1.barh([r["name"] for r in rows], [r["n"] for r in rows], color=HOT, height=.7)
for k, r in enumerate(rows):
    a1.text(r["n"] + 2, k, str(r["n"]), va="center", fontsize=11)
a1.set_xlim(0, 210); a1.set_facecolor(BG); a1.set_title("Biggest embassy networks\n(states with an embassy from...)", fontproperties=F.DISPB, fontsize=16, loc="left")
a2 = fig.add_axes([.6, .25, .36, .15]); s = R["cow"]["series"]; ys = [x["year"] for x in s]
a2.plot(ys, [x["mutual_rep_pairs"] for x in s], color=HOT, lw=2.4, marker="o", ms=3.5, label="pairs of states linked")
a2.plot(ys, [x["states"] * 10 for x in s], color=COOL, lw=2.4, marker="o", ms=3.5, label="states x 10")
a2.set_facecolor(BG); a2.legend(frameon=False, fontsize=11, loc="upper left")
a2.set_title(f"The diplomatic web, {R['cow']['first']} to {R['cow']['last']}", fontproperties=F.DISPB, fontsize=16, loc="left")
a3 = fig.add_axes([.6, .08, .36, .11]); a3.set_facecolor(BG); a3.axis("off")
facts = [f"{R['smallest'][0]['name']}: {R['smallest'][0]['n']} nunciatures for {R['smallest'][0]['pop']:,} people",
         f"{R['longest'][0]['sender']} and {R['longest'][0]['receiver']}: longest embassy link, {R['longest'][0]['km']:,} km",
         f"Israel: {R['israel']['tel_aviv_area']} embassies in the Tel Aviv area, {R['israel']['jerusalem']} in Jerusalem",
         f"New York: {R['switzerland']['new_york_perm_missions']} permanent missions to the United Nations",
         f"Liechtenstein hosts {R['fewest_hosted'][0]['n']} resident embassies",
         f"{R['cow']['first']}: {R['cow']['amb_1817']} of {R['cow']['rep_1817']} links at ambassador rank; {R['cow']['last']}: {R['cow']['amb_share_2005']:.0f}%"]
for k, t in enumerate(facts):
    a3.text(0, 1 - k * .19, "· " + t, fontsize=12.5, color=FG, va="top", transform=a3.transAxes)
for a in (a1, a2):
    for sp in ("top", "right"):
        a.spines[sp].set_visible(False)
fig.text(.04, .022, "Sources: OpenStreetMap contributors (ODbL), Wikidata (CC0), Correlates of War Diplomatic Exchange v2006.1 (Bayer 2006), Natural Earth. "
         "\nMapped missions only: some countries are mapped better than others.", fontsize=11, color=MUT)
fig.text(.04, .009, "Dr Tristan Hotham · maps.tristanhotham.com/embassies", fontsize=11.5, color=FG)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "every_embassy.png")
fig.savefig(out, dpi=160, facecolor=BG)
from PIL import Image
print(out, Image.open(out).size)
