# Every Embassy in the World

The world's embassies, consulates and other diplomatic missions on one interactive map, from OpenStreetMap and Wikidata: 15,584 located missions sent by 198 states, every country's network drawn from its capital, who is present in each capital, per-country coverage notes, and a timeline of the diplomatic web from a sample of famous missions since 2400 BC through the Correlates of War data (1817 to 2005) to today.

Interactive page: https://maps.tristanhotham.com/embassies/
Paper: https://doi.org/10.5281/zenodo.23899269
Blog post: https://blog.tristanhotham.com/2026/10/31/embassies/

## Headline results

- 15,584 missions: 8,917 embassies, 406 high commissions, 92 nunciatures, 148 delegations, 352 permanent missions, 1,857 consulates-general, 1,528 consulates, 1,867 honorary consulates, 239 representative offices, 173 embassy sections; plus 1,191 Wikidata missions without a location, kept as country pairs.
- 9,822 ordered pairs of states have an embassy-level mission (25.2% of possible pairs); 7,099 are in both sources, 1,604 only in OpenStreetMap, 1,154 only in Wikidata.
- Largest embassy-level networks: China 178, United States 168, France 166, United Kingdom 160, Japan 159. Most posts (excluding honorary): United States 279, China 258.
- Checked against the Lowy Institute Global Diplomacy Index 2024 (posts here of Lowy's total): China 258 of 274 (94%); United States 279 of 271 (103%); Turkiye 249 of 252 (99%); Japan 232 of 251 (92%); Indonesia 133 of 130 (102%); Australia 130 of 124 (105%); Taiwan 93 of 110 (85%).
- Most embassies: Washington, D.C. 181, Brussels 178, Paris 170, London 170, Berlin 168. Most career consulates: Barcelona 83, Istanbul 73. Densest kilometre: New York around the UN (182), Washington (95).
- Embassies that did not follow the capital: Israel 79 in the Tel Aviv area and 3 in Jerusalem; Bolivia 33 in La Paz, none in Sucre; Tanzania 61 in Dar es Salaam; Myanmar 46 in Yangon. Lagos keeps 24 consulates; Bern 85 embassies, Geneva 58 permanent missions.
- Small states: the Holy See has 88 nunciatures for about 825 people; Liechtenstein hosts no resident embassy. Longest embassy link: Taiwan and Paraguay, 19,931 km.
- Contested cases, as recorded: Taiwanese embassies in all 12 states that recognise Taiwan and 52 representative offices; 13 out-of-date Taiwan embassy records flagged and excluded. 25 embassies mapped in Pristina. 24 missions to Palestine, 22 in the Ramallah area. Only 2 consulates mapped in Western Sahara (a coverage gap).
- 1817 to 2005 (Correlates of War): 23 to 192 states; 198 to 8,110 directed links; ambassador share 11.6% to 92.7%. West Germany 93 and East Germany 12 states in 1965; PRC 93 and Taiwan 24 in 1975.
- Deep history: a sample of 52 famous missions and milestones (60 lines) from 2400 BC to 1815; dates checked against the cited Wikipedia articles: 42 confirmed, 10 approximate, 8 not confirmed.
- Coverage: by the 2005 benchmark the network abroad looks complete for 185 of 190 countries; thinnest hosted: Somalia, Central African Republic, Tuvalu, Saint Vincent and the Grenadines.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; results embedded, map data fetched from `data/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/missions.csv`, `data/missions.geojson` | The mission gazetteer: id (OSM n/w/r id or Wikidata QID), source, type, sender, receiver, host territory, city, coordinates, names, Wikidata id, website, Wikidata opening year, how the sender was found, sub-national flag, merged duplicates. ODbL. |
| `data/wikidata_unlocated.csv` | Wikidata missions without coordinates (country pairs only). |
| `data/dyads.csv` | Every sending and receiving pair with counts by level and source, and the 2005 Correlates of War flag. |
| `data/country_summary.csv` | Per-country counts, the 2005 benchmark, coverage flags and notes. |
| `data/countries.csv` | The 198 states and entities, with capitals or seats of government used for lines. |
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

- OpenStreetMap: 17,573 objects tagged office=diplomatic or amenity=embassy (Overpass, 2026). Typed from tags and names; residences (775), international organisation offices (84), unknown senders (289) and non-diplomatic objects (564) dropped. Sender from the country tag, linked Wikidata item or name; receiver is the territory where the mission stands (Natural Earth 1:10m), except embassies to the Holy See and permanent missions. Duplicates within 350 m merged (352).
- Wikidata: two requested classes were schools and television channels and were dropped; embassy, consulate and representative office items linked through OSM wikidata tags (5,731), matched by country pair (1,722), added with coordinates (81) or kept unlocated (1,191); items with end dates dropped (244).
- Corrections: Taiwan records checked against the 12 states that recognise it (Reuters, 2026); 3 hand corrections in the merge log.
- Coverage: 2026 embassy-level pairs against states with representation in the 2005 Correlates of War data (good at 0.8 or more, thin below 0.5); Lowy totals for seven countries.
- History: Correlates of War Diplomatic Exchange v2006.1; levels not recorded 1950 to 1965. Deep history: hand-compiled, conventional dates, each checked against its cited Wikipedia article (42 confirmed, 10 approximate, 8 not confirmed); `data/deep_history.csv` holds the authoritative status per line and is read, never overwritten, by `code/03b_deep.py`.
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

Hotham, T. (2026) Every Embassy in the World: the world's diplomatic missions from open data, and the diplomatic web from the Amarna letters to today. Zenodo. https://doi.org/10.5281/zenodo.23899269

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
