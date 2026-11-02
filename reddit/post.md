## Title

[OC] Every embassy in the world: 15,584 embassies, consulates and missions mapped from open data. Washington hosts 181 embassies; the Holy See, population 825, runs 88

## Body

I merged OpenStreetMap's diplomatic buildings with Wikidata's list of embassies and cleaned the result into 15,584 current missions sent by 198 states. To check it, I compared total posts with the Lowy Institute's Global Diplomacy Index: for the seven countries it publishes, this map finds 85% to 105% of Lowy's count. China has embassy-level missions in the most states (178), the United States the most posts overall (279). Barcelona has more career consulates than any other city (83). Some capitals never got their embassies: Bolivia's 33 are all in La Paz rather than Sucre, Tanzania's in Dar es Salaam rather than Dodoma. The interactive version draws any country's network from its capital and plays the diplomatic web from the Amarna letters through the Correlates of War data (1817 to 2005) to today. Caveats: a dot is a mapped mission, not proof it is open; consulates and honorary consulates are mapped unevenly; contested cases are shown as the data record them. Interactive map: https://maps.tristanhotham.com/embassies/

## Source comment

Sources: OpenStreetMap contributors (office=diplomatic, ODbL), Wikidata (CC0), Correlates of War Diplomatic Exchange v2006.1 (Bayer 2006), Lowy Institute Global Diplomacy Index 2024 (for checking), Natural Earth.

Tools: Python (pandas, shapely, matplotlib); Leaflet and Supercluster for the interactive map.

Interactive version: https://maps.tristanhotham.com/embassies/
Paper: https://doi.org/10.5281/zenodo.23899269
Blog post: https://blog.tristanhotham.com/2026/10/31/embassies/
