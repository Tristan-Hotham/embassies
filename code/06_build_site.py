"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json, which is embedded; map data (data/points.json, site.json, world.json, cow_timeline.json) is fetched by
the page. Facts stated in words are checked here. 10.5281/zenodo.23899269 and https://blog.tristanhotham.com/2026/10/31/embassies/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "BLOG_URL", "DOI_URL"}

# ---- facts stated in words (page, blog, paper, collage) ----
C, N = R["cities"], R["networks"]
assert C[0]["city"].startswith("Washington") and C[1]["city"] == "Brussels" and C[2]["n"] == C[3]["n"] and {C[2]["city"], C[3]["city"]} == {"Paris", "London"}
assert C[4]["city"] == "Berlin" and C[5]["city"] == "Rome"
assert N["embassies"][0]["code"] == "CN" and N["embassies"][1]["code"] == "US" and N["posts"][0]["code"] == "US" and N["posts"][1]["code"] == "CN"
assert R["coverage"]["lowy"][0]["code"] == "CN" and R["coverage"]["lowy"][1]["code"] == "US"
assert R["consular_cities"][0]["city"] == "Barcelona" and R["consular_cities"][1]["city"] == "Istanbul"
assert R["clusters"][0]["city"] == "New York" and R["clusters"][1]["city"].startswith("Washington") and R["clusters"][2]["city"] == "Beijing"
assert R["smallest"][0]["code"] == "VA" and R["smallest"][4]["code"] == "SM" and R["smallest"][6]["code"] == "MC" and R["smallest"][1]["code"] == "TV"
assert R["smallest"][0]["n"] > 50                                                     # "more than many large countries"
assert R["fewest_hosted"][0]["code"] == "LI" and R["fewest_hosted"][0]["n"] == 0
assert R["fewest_hosted"][2]["n"] == R["fewest_hosted"][3]["n"] == R["fewest_hosted"][4]["n"] == 1
assert {R["longest"][0]["sender"], R["longest"][0]["receiver"]} == {"Taiwan", "Paraguay"} and R["longest"][0]["km"] > 19500   # nearly antipodal
nb = {frozenset(x["codes"]) for x in R["neighbours"]["list"]}
for a, b in (("KP", "KR"), ("AM", "AZ"), ("AM", "TR"), ("IL", "LB"), ("IL", "SY"), ("IL", "PS"), ("RS", "XK"), ("MA", "EH"), ("BW", "NA")):
    assert frozenset((a, b)) in nb, (a, b)
assert next(x for x in R["neighbours"]["list"] if set(x["codes"]) == {"BW", "NA"})["cow2005_directions"] == 2
I = R["israel"]
assert I["jerusalem_senders"] == ["Guatemala", "Kosovo", "United States"] and I["jerusalem"] == 3 and I["tel_aviv_area"] > 0.9 * I["embassies"]
assert R["palestine"]["ramallah_area"] > R["palestine"]["missions_to"] / 2                                  # "most in Ramallah"
mv = R["moves"]
assert mv["bolivia"]["emb_new"] == 0 and mv["bolivia"]["emb_old"] == mv["bolivia"]["embassies"]
assert mv["netherlands"]["emb_new"] == 0 and mv["tanzania"]["emb_new"] == 0 and mv["ivory_coast"]["emb_new"] == 0 and mv["myanmar"]["emb_new"] == 0
assert mv["tanzania"]["emb_old"] == mv["tanzania"]["embassies"] and mv["ivory_coast"]["emb_old"] == mv["ivory_coast"]["embassies"]
assert mv["turkey"]["emb_new"] == mv["turkey"]["embassies"] and mv["nigeria"]["cons_old"] > mv["nigeria"]["cons_new"]
assert R["switzerland"]["bern"] > 0.95 * R["switzerland"]["embassies"]
assert R["holy_see"]["embassies_to_in_rome"] == R["holy_see"]["embassies_to"]
assert R["taiwan"]["n_embassy_hosts"] == R["taiwan"]["allies_n"] == 12
assert set(R["data"]["flagged_states"]) == {"Honduras", "Nicaragua", "Nauru", "Kiribati", "El Salvador", "Burkina Faso", "Sao Tome and Principe"}, R["data"]["flagged_states"]
assert R["western_sahara"]["missions_in_territory"] == 2 and list(R["western_sahara"]["cities"]) == ["Laayoune"]
assert R["eu"]["delegations"] > 100
assert (R["deep"]["confirmed"], R["deep"]["approximate"], R["deep"]["not_confirmed"]) == (42, 10, 8)
assert R["cow"]["top_host_1817"][0] == "France" and R["cow"]["net"]["1817"]["hosts"][1][0] == "United Kingdom"
h17 = dict(R["cow"]["net"]["1817"]["hosts"]); assert h17["Two Sicilies"] >= h17["United Kingdom"] - 1 and h17["Bavaria"] >= h17["United Kingdom"] - 1     # "almost as many as London"
assert R["cow"]["peak_rep_year"] == 1980 and R["cow"]["rep_1985"] < R["cow"]["rep_1980"]
assert all(r["a"] > r["b"] for r in R["cow"]["splits"]["us_ussr"])                                         # US ahead in every wave
assert R["cow"]["prc_roc_both_max"] <= 1                                                                    # "never shared a host" (one wave records one, a coding overlap)
assert R["cow"]["roc_1950"] > R["cow"]["prc_1950"] and R["cow"]["prc_1975"] > R["cow"]["roc_1975"]
assert R["coverage"]["lowy_min_pct"] >= 85 and R["coverage"]["lowy_max_pct"] <= 110
assert R["coverage"]["thin_hosted_list"][:4] == ["Somalia", "Central African Republic", "Tuvalu", "Saint Vincent and the Grenadines"]


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\}|DOI_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = set(re.findall(r"\{\{([^}]*)\}\}", html))
    assert left <= KEEP, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
