"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json. 10.5281/zenodo.23899269 and https://blog.tristanhotham.com/2026/10/31/embassies/ stay as placeholders."""
from common import *

R = jload(f"{DATA}/results.json")
D, N, C, P = R["data"], R["networks"], R["cities"], R["pairs"]
cw, dp = R["cow"], R["deep"]
lowy = "; ".join(f"{x['name']} {x['here']} of {x['lowy']} ({x['pct']}%)" for x in R["coverage"]["lowy"])
readme = f"""# Every Embassy in the World

The world's embassies, consulates and other diplomatic missions on one interactive map, from OpenStreetMap and Wikidata: {D['missions']:,} located missions sent by {D['senders']} states, every country's network drawn from its capital, who is present in each capital, per-country coverage notes, and a timeline of the diplomatic web from a sample of famous missions since {fmt(dp['first_year'], 'yr')} through the Correlates of War data (1817 to 2005) to today.

Interactive page: https://maps.tristanhotham.com/embassies/
Paper: https://doi.org/{{10.5281/zenodo.23899269}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/embassies/}}

## Headline results

- {D['missions']:,} missions: {D['by_type']['embassy']:,} embassies, {D['by_type']['high_commission']} high commissions, {D['by_type']['nunciature']} nunciatures, {D['by_type']['delegation']} delegations, {D['by_type']['perm_mission']} permanent missions, {D['by_type']['consulate_general']:,} consulates-general, {D['by_type']['consulate']:,} consulates, {D['by_type']['honorary']:,} honorary consulates, {D['by_type']['liaison']} representative offices, {D['by_type']['embassy_office']} embassy sections; plus {D['wd_unlocated']:,} Wikidata missions without a location, kept as country pairs.
- {P['resident_states']:,} ordered pairs of states have an embassy-level mission ({P['density_pc']}% of possible pairs); {P['both']:,} are in both sources, {P['osm_only']:,} only in OpenStreetMap, {P['wd_only']:,} only in Wikidata.
- Largest embassy-level networks: {', '.join(f"{x['name']} {x['n']}" for x in N['embassies'][:5])}. Most posts (excluding honorary): {N['posts'][0]['name']} {N['posts'][0]['n']}, {N['posts'][1]['name']} {N['posts'][1]['n']}.
- Checked against the Lowy Institute Global Diplomacy Index 2024 (posts here of Lowy's total): {lowy}.
- Most embassies: {', '.join(f"{x['city']} {x['n']}" for x in C[:5])}. Most career consulates: {R['consular_cities'][0]['city']} {R['consular_cities'][0]['n']}, {R['consular_cities'][1]['city']} {R['consular_cities'][1]['n']}. Densest kilometre: New York around the UN ({R['clusters'][0]['n']}), Washington ({R['clusters'][1]['n']}).
- Embassies that did not follow the capital: Israel {R['israel']['tel_aviv_area']} in the Tel Aviv area and {R['israel']['jerusalem']} in Jerusalem; Bolivia {R['moves']['bolivia']['emb_old']} in La Paz, none in Sucre; Tanzania {R['moves']['tanzania']['emb_old']} in Dar es Salaam; Myanmar {R['moves']['myanmar']['emb_old']} in Yangon. Lagos keeps {R['moves']['nigeria']['cons_old']} consulates; Bern {R['switzerland']['bern']} embassies, Geneva {R['switzerland']['geneva_perm_missions']} permanent missions.
- Small states: the Holy See has {R['smallest'][0]['n']} nunciatures for about {R['smallest'][0]['pop']} people; Liechtenstein hosts no resident embassy. Longest embassy link: {R['longest'][0]['sender']} and {R['longest'][0]['receiver']}, {R['longest'][0]['km']:,} km.
- Contested cases, as recorded: Taiwanese embassies in all {R['taiwan']['n_embassy_hosts']} states that recognise Taiwan and {R['taiwan']['by_type']['liaison']} representative offices; {D['flagged']} out-of-date Taiwan embassy records flagged and excluded. {R['kosovo']['embassies_hosted']} embassies mapped in Pristina. {R['palestine']['missions_to']} missions to Palestine, {R['palestine']['ramallah_area']} in the Ramallah area. Only {R['western_sahara']['missions_in_territory']} consulates mapped in Western Sahara (a coverage gap).
- 1817 to 2005 (Correlates of War): {cw['states_1817']} to {cw['states_2005']} states; {cw['rep_1817']} to {cw['rep_2005']:,} directed links; ambassador share {cw['amb_share_1817']}% to {cw['amb_share_2005']}%. West Germany {cw['frg_1965']} and East Germany {cw['gdr_1965']} states in 1965; PRC {cw['prc_1975']} and Taiwan {cw['roc_1975']} in 1975.
- Deep history: a sample of {dp['events']} famous missions and milestones ({dp['entries']} lines) from {fmt(dp['first_year'], 'yr')} to {dp['last_year']}; dates checked against the cited Wikipedia articles: {dp['confirmed']} confirmed, {dp['approximate']} approximate, {dp['not_confirmed']} not confirmed.
- Coverage: by the 2005 benchmark the network abroad looks complete for {R['coverage']['abroad_good']} of {R['coverage']['benchmarked']} countries; thinnest hosted: {', '.join(R['coverage']['thin_hosted_list'][:4])}.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; results embedded, map data fetched from `data/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/missions.csv`, `data/missions.geojson` | The mission gazetteer: id (OSM n/w/r id or Wikidata QID), source, type, sender, receiver, host territory, city, coordinates, names, Wikidata id, website, Wikidata opening year, how the sender was found, sub-national flag, merged duplicates. ODbL. |
| `data/wikidata_unlocated.csv` | Wikidata missions without coordinates (country pairs only). |
| `data/dyads.csv` | Every sending and receiving pair with counts by level and source, and the 2005 Correlates of War flag. |
| `data/country_summary.csv` | Per-country counts, the 2005 benchmark, coverage flags and notes. |
| `data/countries.csv` | The {R['countries']['states']} states and entities, with capitals or seats of government used for lines. |
| `data/flagged_out_of_date.csv` | Records excluded as out of date. |
| `data/deep_history.csv`, `data/deep_history.json` | The deep-history sample with sources and status. |
| `data/cow_timeline.json` | Correlates of War timeline for the page (states, capitals, pair bitmasks, series). |
| `data/results.json` | Every number quoted on the page, in the paper, blog, collage and post. |
| `data/points.json`, `data/site.json`, `data/world.json`, `data/today_pairs.json` | Page data. |
| `data/merge_log.json` | Counts of every cleaning step, corrections and examples. |
| `code/` | Scripts, run in order; `deep_history.py` (the hand-compiled sample); page, paper and blog templates; `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, `every_embassy.png`) and post text. |

## Method in brief

- OpenStreetMap: {D['osm_features']:,} objects tagged office=diplomatic or amenity=embassy (Overpass, 2026). Typed from tags and names; residences ({D['dropped_residences']}), international organisation offices ({D['dropped_intl_org']}), unknown senders ({D['dropped_unknown_sender']}) and non-diplomatic objects ({D['dropped_other']}) dropped. Sender from the country tag, linked Wikidata item or name; receiver is the territory where the mission stands (Natural Earth 1:10m), except embassies to the Holy See and permanent missions. Duplicates within {R['params']['merge_m']} m merged ({D['merged_dups']}).
- Wikidata: two requested classes were schools and television channels and were dropped; embassy, consulate and representative office items linked through OSM wikidata tags ({D['wd_linked']:,}), matched by country pair ({D['wd_matched']:,}), added with coordinates ({D['wd_added']}) or kept unlocated ({D['wd_unlocated']:,}); items with end dates dropped ({D['wd_dropped_dissolved']}).
- Corrections: Taiwan records checked against the {R['taiwan']['allies_n']} states that recognise it (Reuters, 2026); {D['hand_corrections']} hand corrections in the merge log.
- Coverage: 2026 embassy-level pairs against states with representation in the 2005 Correlates of War data (good at 0.8 or more, thin below 0.5); Lowy totals for seven countries.
- History: Correlates of War Diplomatic Exchange v2006.1; levels not recorded 1950 to 1965. Deep history: hand-compiled, conventional dates, each checked against its cited Wikipedia article ({dp['confirmed']} confirmed, {dp['approximate']} approximate, {dp['not_confirmed']} not confirmed); `data/deep_history.csv` holds the authoritative status per line and is read, never overwritten, by `code/03b_deep.py`.
- Caveats: mapped is not the same as open; consulates and honorary consulates are mapped unevenly; non-resident accreditation is invisible; contested cases are described as the data record them.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib, Pillow and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw input paths are in `code/common.py`. Intermediate files go to `/dev/shm/embassies/work` (set `EMBTMP` to change).

```
python3 code/01_countries.py     # states, names, capitals, territories
python3 code/02_gazetteer.py     # OSM + Wikidata: data/missions.*, merge log
python3 code/03_cow.py           # Correlates of War timeline
python3 code/03b_deep.py         # deep-history sample
python3 code/04_results.py       # data/results.json, dyads, country summary
python3 code/05_site_data.py     # page data
python3 code/06_build_site.py    # index.html
python3 code/07_figures.py       # header, blog and paper figures
python3 code/08_paper.py         # paper PDF
python3 reddit/collage.py        # collage
python3 code/09_readme.py        # README, LICENSE, Reddit post
python3 code/10_release.py       # blog post, Zenodo files
```

## Sources and licences

- © OpenStreetMap contributors, Open Database License 1.0. The mission gazetteer (`data/missions.*`, `data/points.json`, `data/dyads.csv`) is a derived database released under the ODbL.
- Wikidata (CC0).
- Bayer, Resat (2006) Diplomatic Exchange Data set, v2006.1. Correlates of War Project, http://correlatesofwar.org. COW State System Membership list (2011) for names.
- Lowy Institute Global Diplomacy Index 2024, key findings (totals quoted only). Reuters (2026) factbox on Taiwan's diplomatic allies.
- Natural Earth (public domain). Leaflet (BSD-2), Supercluster (ISC). Base maps on the page © Esri.

## Licence

Code: MIT. Text, figures and most derived data: CC BY 4.0. Not CC BY: the mission gazetteer and every file derived from OpenStreetMap (`data/missions.csv`, `data/missions.geojson`, `data/points.json`, `data/dyads.csv`, `data/site.json`, `data/country_summary.csv`, `data/today_pairs.json`) is released under the Open Database License 1.0 (ODbL), © OpenStreetMap contributors; Wikidata content is CC0; `data/cow_timeline.json` derives from the Correlates of War Diplomatic Exchange data (free to use with citation of Bayer 2006); the deep-history notes cite English Wikipedia articles (CC BY-SA 4.0) but contain no copied text. See `LICENSE`.

## Citation

Hotham, T. (2026) Every Embassy in the World: the world's diplomatic missions from open data, and the diplomatic web from the Amarna letters to today. Zenodo. https://doi.org/{{10.5281/zenodo.23899269}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in readme.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/ptolemy/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post and the figures are released under
CC BY 4.0. The mission gazetteer and files derived from OpenStreetMap
(data/missions.csv, data/missions.geojson, data/points.json, data/dyads.csv,
data/site.json, data/country_summary.csv, data/today_pairs.json) are released
under the Open Database License 1.0 (ODbL); map data (c) OpenStreetMap
contributors. Wikidata content is CC0. Other derived data are CC BY 4.0;
data/cow_timeline.json is derived from the Correlates of War Diplomatic
Exchange data (Bayer 2006), please cite it. Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Every embassy in the world: {D['missions']:,} embassies, consulates and missions mapped from open data. Washington hosts {C[0]['n']} embassies; the Holy See, population {R['smallest'][0]['pop']}, runs {R['smallest'][0]['n']}

## Body

I merged OpenStreetMap's diplomatic buildings with Wikidata's list of embassies and cleaned the result into {D['missions']:,} current missions sent by {D['senders']} states. To check it, I compared total posts with the Lowy Institute's Global Diplomacy Index: for the seven countries it publishes, this map finds {R['coverage']['lowy_min_pct']}% to {R['coverage']['lowy_max_pct']}% of Lowy's count. {N['embassies'][0]['name']} has embassy-level missions in the most states ({N['embassies'][0]['n']}), the United States the most posts overall ({N['posts'][0]['n']}). {R['consular_cities'][0]['city']} has more career consulates than any other city ({R['consular_cities'][0]['n']}). Some capitals never got their embassies: Bolivia's {R['moves']['bolivia']['emb_old']} are all in La Paz rather than Sucre, Tanzania's in Dar es Salaam rather than Dodoma. The interactive version draws any country's network from its capital and plays the diplomatic web from the Amarna letters through the Correlates of War data (1817 to 2005) to today. Caveats: a dot is a mapped mission, not proof it is open; consulates and honorary consulates are mapped unevenly; contested cases are shown as the data record them. Interactive map: https://maps.tristanhotham.com/embassies/

## Source comment

Sources: OpenStreetMap contributors (office=diplomatic, ODbL), Wikidata (CC0), Correlates of War Diplomatic Exchange v2006.1 (Bayer 2006), Lowy Institute Global Diplomacy Index 2024 (for checking), Natural Earth.

Tools: Python (pandas, shapely, matplotlib); Leaflet and Supercluster for the interactive map.

Interactive version: https://maps.tristanhotham.com/embassies/
Paper: https://doi.org/{{10.5281/zenodo.23899269}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/embassies/}}
"""
for bad in ("—", "–", "--"):
    assert bad not in post, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README, LICENSE, post.md written")
