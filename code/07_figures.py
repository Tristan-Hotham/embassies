"""Static figures: header.png (1200 x 630), blog figures (release/blog/b_*.png, 1800 px wide) and paper figures
(release/paper/f_*.png). House fonts (Fraunces cut to static instances, IBM Plex Mono, Source Serif 4), light paper."""
import pickle, shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection
from shapely.geometry import shape
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf"); DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
plt.rcParams.update({"font.family": "IBM Plex Mono", "font.size": 12, "axes.edgecolor": "#656170", "axes.labelcolor": "#1E2230",
                     "xtick.color": "#656170", "ytick.color": "#656170"})
BG, FG, MUT, RULE, LAND = "#F7F3EA", "#1E2230", "#656170", "#E2D9C7", "#E6DFD0"
HOT, COOL, GOLD = "#B3261E", "#1F5FAD", "#C98A00"
GRPCOL = {"resident": "#B3261E", "consular": "#E07B39", "liaison": "#2E8B57", "honorary": "#8E9BAA", "multilateral": "#0E7C7B", "office": "#B8A27A"}
R = jload(f"{DATA}/results.json")
G = pickle.load(open(f"{WORK}/gaz.pkl", "rb")); M = G["M"]
Cc = pickle.load(open(f"{WORK}/countries.pkl", "rb")); S = Cc["S"]
BLOG = os.path.join(ROOT, "release", "blog"); PAP = os.path.join(ROOT, "release", "paper")
for d in (BLOG, PAP):
    os.makedirs(d, exist_ok=True)
LANDG = [shape(f["geometry"]) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]]


def draw_land(ax, color=LAND, edge="#CFC6B4"):
    for g in LANDG:
        for p in getattr(g, "geoms", [g]):
            x, y = p.exterior.xy
            ax.fill(x, y, color=color, ec=edge, lw=.3, zorder=1)
    ax.set_xlim(-180, 180); ax.set_ylim(-58, 84); ax.set_aspect("equal"); ax.axis("off")


def gcl(a, b, n=40):
    la1, lo1, la2, lo2 = map(np.radians, (a[0], a[1], b[0], b[1]))
    d = 2 * np.arcsin(np.sqrt(np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2))
    if d < 1e-6:
        return [[a[1], a[0]], [b[1], b[0]]]
    f = np.linspace(0, 1, n); A = np.sin((1 - f) * d) / np.sin(d); B = np.sin(f * d) / np.sin(d)
    x = A * np.cos(la1) * np.cos(lo1) + B * np.cos(la2) * np.cos(lo2); y = A * np.cos(la1) * np.sin(lo1) + B * np.cos(la2) * np.sin(lo2)
    z = A * np.sin(la1) + B * np.sin(la2)
    lat = np.degrees(np.arctan2(z, np.sqrt(x * x + y * y))); lon = np.degrees(np.arctan2(y, x))
    return np.column_stack([lon, lat])


def segs(line):
    """Split a lon/lat polyline where it jumps across the 180 degree meridian."""
    out, cur = [], [line[0]]
    for p, q in zip(line[:-1], line[1:]):
        if abs(q[0] - p[0]) > 180:
            out.append(cur); cur = []
        cur.append(q)
    out.append(cur)
    return [np.array(s) for s in out if len(s) > 1]


def save(fig, name, blog=True, paper=True):
    if blog:
        fig.savefig(f"{BLOG}/b_{name}.png", dpi=150, facecolor=fig.get_facecolor())
    if paper:
        fig.savefig(f"{PAP}/f_{name}.png", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def grp(m):
    return TYPES[m["type"]][1]


def fig_map():
    fig = plt.figure(figsize=(12, 6.2), facecolor=BG); ax = fig.add_axes([0, .02, 1, .96]); ax.set_facecolor(BG)
    draw_land(ax)
    for g in ("honorary", "liaison", "multilateral", "consular", "resident"):
        pts = np.array([[m["lon"], m["lat"]] for m in M if grp(m) == g and not m["subnational"]])
        ax.scatter(pts[:, 0], pts[:, 1], s=2.2 if g == "resident" else 1.6, c=GRPCOL[g], lw=0, alpha=.75, zorder=3)
    ax.text(-178, -55, f"{R['data']['missions']:,} missions. Red: embassy level; orange: consulates; grey: honorary; green: representative offices; teal: permanent missions.",
            fontsize=9.5, color=MUT, zorder=5)
    save(fig, "map")


def fig_networks():
    rows = R["networks"]["embassies"][:15][::-1]
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG); ax.set_facecolor(BG)
    ax.barh([r["name"] for r in rows], [r["n"] for r in rows], color=HOT, height=.68)
    for k, r in enumerate(rows):
        ax.text(r["n"] + 1.5, k, str(r["n"]), va="center", fontsize=11, color=FG)
    ax.set_xlabel("States with an embassy, high commission or nunciature from this country")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(0, 200); fig.tight_layout(); save(fig, "networks")


def fig_cities():
    rows = R["cities"][:15][::-1]
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG); ax.set_facecolor(BG)
    ax.barh([r["city"] for r in rows], [r["n"] for r in rows], color=COOL, height=.68)
    for k, r in enumerate(rows):
        ax.text(r["n"] + 1.5, k, str(r["n"]), va="center", fontsize=11)
    ax.set_xlabel("Embassy-level missions accredited to the host country")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(0, 200); fig.tight_layout(); save(fig, "cities")


def network_lines(code):
    o = S[code]["capital"]; o = (o["lat"], o["lon"])
    ls, cs = [], []
    for m in M:
        if m["sender"] == code and not m["subnational"] and grp(m) in GRPCOL:
            for s in segs(gcl(o, (m["lat"], m["lon"]))):
                ls.append(s); cs.append(GRPCOL[grp(m)])
    for w in G["unlocated"]:
        if w["sender"] == code and w["receiver"] in S:
            c = S[w["receiver"]]["capital"]
            for s in segs(gcl(o, (c["lat"], c["lon"]))):
                ls.append(s); cs.append(GRPCOL[TYPES[w["type"]][1]])
    return o, ls, cs


def fig_examples():
    fig, axs = plt.subplots(2, 2, figsize=(12, 6.6), facecolor=BG)
    for ax, code in zip(axs.flat, ("CN", "US", "VA", "TW")):
        ax.set_facecolor(BG); draw_land(ax)
        o, ls, cs = network_lines(code)
        ax.add_collection(LineCollection(ls, colors=cs, linewidths=.6, alpha=.6, zorder=3))
        ax.scatter([o[1]], [o[0]], s=26, c=FG, zorder=5, edgecolors="white", linewidths=.8)
        n = sum(1 for m in M if m["sender"] == code and not m["subnational"])
        ax.set_title(f"{S[code]['name']}: {n} missions mapped", fontproperties=DISPB, fontsize=14, loc="left", color=FG)
    fig.text(.01, .01, "Lines from the capital to each mission. Red embassy level, orange consulates, green representative offices, grey honorary.", fontsize=9.5, color=MUT)
    fig.tight_layout(rect=(0, .03, 1, 1)); save(fig, "examples")


def fig_web():
    S_ = R["cow"]["series"]; ys = [s["year"] for s in S_]
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.2), facecolor=BG)
    for ax, key, col, t, ym in ((axs[0], "states", COOL, "States in the system", 200), (axs[1], "mutual_rep_pairs", HOT, "Pairs linked", 4000),
                                (axs[2], "amb_share", GOLD, "Share at ambassador rank (%)", 100)):
        ax.set_facecolor(BG); v = [s[key] for s in S_]
        ax.plot(ys, [np.nan if x is None else x for x in v], color=col, lw=2.2, marker="o", ms=3)
        ax.axvspan(1948, 1967, color="#EEE7D8", zorder=0); ax.set_ylim(0, ym); ax.set_title(t, fontproperties=DISPB, fontsize=13, loc="left")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axs[2].text(1957, 50, "no levels\nrecorded", ha="center", fontsize=8.5, color=MUT)
    fig.text(.01, .01, "Correlates of War Diplomatic Exchange v2006.1 (Bayer 2006).", fontsize=9, color=MUT)
    fig.tight_layout(rect=(0, .04, 1, 1)); save(fig, "web")


def fig_rivals():
    sp = R["cow"]["splits"]
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.2), facecolor=BG)
    for ax, (k, la, lb, t) in zip(axs, (("us_ussr", "United States", "Soviet Union", "US and USSR"), ("prc_roc", "People's Republic", "Taiwan (ROC)", "China and Taiwan"),
                                        ("frg_gdr", "West Germany", "East Germany", "The two Germanys"))):
        rows = [r for r in sp[k] if not (k == "frg_gdr" and r["year"] >= 1990)]
        ax.set_facecolor(BG); y = [r["year"] for r in rows]
        ax.plot(y, [r["a"] for r in rows], color=COOL if k != "prc_roc" else HOT, lw=2.2, marker="o", ms=3, label=la)
        ax.plot(y, [r["b"] for r in rows], color=HOT if k != "prc_roc" else COOL, lw=2.2, marker="o", ms=3, label=lb)
        ax.set_ylim(0, 180); ax.set_title(t, fontproperties=DISPB, fontsize=13, loc="left"); ax.legend(frameon=False, fontsize=9, loc="upper left")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.text(.01, .01, "Number of states in which each side was represented. Correlates of War Diplomatic Exchange v2006.1.", fontsize=9, color=MUT)
    fig.tight_layout(rect=(0, .04, 1, 1)); save(fig, "rivals")


def fig_deep():
    D = jload(f"{DATA}/deep_history.json")["entries"]
    fig = plt.figure(figsize=(12, 6), facecolor=BG); ax = fig.add_axes([0, .1, 1, .9]); ax.set_facecolor(BG)
    draw_land(ax); ax.set_xlim(-12, 145); ax.set_ylim(-12, 62)
    cmap = plt.get_cmap("plasma")
    for e in D:
        t = (e["year"] + 2400) / (1815 + 2400)
        for s in segs(gcl((e["lat1"], e["lon1"]), (e["lat2"], e["lon2"]))):
            ax.plot(s[:, 0], s[:, 1], color=cmap(.05 + .85 * t), lw=2.4 if e["kind"] == "resident" else 1.4, alpha=.85, zorder=3)
        ax.scatter([e["lon1"], e["lon2"]], [e["lat1"], e["lat2"]], s=10, c=FG, zorder=4)
    for y, lab in ((-2400, "2400 BC"), (-1350, "1350 BC"), (166, "AD 166"), (1000, "1000"), (1446, "1446"), (1815, "1815")):
        pass
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(-2400, 1815)); cax = fig.add_axes([.64, .1, .32, .022])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal"); cb.set_ticks([-2000, -1000, 0, 1000]); cb.set_ticklabels(["2000 BC", "1000 BC", "AD 1", "1000"])
    cb.outline.set_visible(False); cax.tick_params(labelsize=9)
    fig.text(.01, .015, f"A sample of {R['deep']['entries']} famous missions, letters, treaties and congresses before 1817 ({R['deep']['confirmed']} dates confirmed in the cited article, {R['deep']['approximate']} approximate, {R['deep']['not_confirmed']} not confirmed).", fontsize=9.5, color=MUT)
    save(fig, "deep")


def header():
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
    ax = fig.add_axes([.38, .06, .62, .88]); ax.set_facecolor(BG); draw_land(ax, edge="none"); ax.set_xlim(-130, 160); ax.set_ylim(-50, 75)
    o, ls, cs = network_lines("CN")
    pts = np.array([[m["lon"], m["lat"]] for m in M if grp(m) == "resident"])
    ax.scatter(pts[:, 0], pts[:, 1], s=1.2, c=HOT, lw=0, alpha=.7, zorder=3)
    o, ls, cs = network_lines("VA")
    ax.add_collection(LineCollection(ls, colors=GOLD, linewidths=.7, alpha=.75, zorder=4))
    fig.text(.04, .74, "Every", fontproperties=DISP, fontsize=58, color=FG)
    fig.text(.04, .57, "Embassy", fontproperties=DISP, fontsize=58, color=HOT)
    fig.text(.04, .40, "in the World", fontproperties=DISP, fontsize=46, color=FG)
    fig.text(.045, .27, f"{R['data']['missions']:,} missions mapped", fontsize=15, color=FG)
    fig.text(.045, .21, f"{R['cities'][0]['city']}: {R['cities'][0]['n']} embassies", fontsize=13, color=MUT)
    fig.text(.045, .16, f"Diplomacy from {yr(R['deep']['first_year'])} to today", fontsize=13, color=MUT)
    fig.text(.045, .06, "maps.tristanhotham.com/embassies", fontsize=11, color=MUT)
    fig.text(.70, .04, "Gold: Holy See nunciatures. Red: embassies.", fontsize=9, color=MUT)
    fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)


def yr(y):
    return f"{-y} BC" if y < 0 else str(y)


if __name__ == "__main__":
    for f in (fig_map, fig_networks, fig_cities, fig_examples, fig_web, fig_rivals, fig_deep, header):
        f(); print(f.__name__)
    from PIL import Image
    print(Image.open(os.path.join(ROOT, "header.png")).size, [Image.open(f"{BLOG}/{f}").size for f in sorted(os.listdir(BLOG)) if f.endswith(".png")])
