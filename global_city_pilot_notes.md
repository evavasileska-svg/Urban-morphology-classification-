# Global City Pilot Notes

## Goal

Test extra OpenStreetMap data from African, Asian, and American cities.

This is a separate global comparison dataset.

It should not overwrite the main European Urban Atlas dataset.

---

## Branch

Branch name:

`eduardo-global-osm-cities`

Purpose:

Keep global city experiments separate from team files.

---

## Team-safe rule

Do not edit or overwrite the main processed files:

- `data/processed/patch_centres.csv`
- `data/processed/graph_features.csv`
- `data/processed/building_features.csv`
- `data/processed/terrain_poi_features.csv`
- `data/processed/entropy_features.csv`
- `data/processed/dataset_assembled.csv`

Use separate global folders:

- `data/raw_global/`
- `data/processed_global/`

---

## Dataset role

Main European dataset:

- supervised dataset
- uses Urban Atlas labels
- used for training and classification

Global OSM dataset:

- unlabeled comparison dataset
- uses African, Asian, and American city patches
- used to test feature-space generalization
- used to check city and continent bias

---

## Pilot cities

Africa:

- Cairo, Egypt
- Marrakesh, Morocco

Asia:

- Tokyo, Japan
- Bangkok, Thailand

Americas:

- New York City, USA
- Mexico City, Mexico

---

## Patch strategy

Patch size:

`500m x 500m`

Grid step:

`250m`

Original full patch count:

`9,000`

Balanced pilot sample:

`600 patches`

Sampling rule:

`100 patches per city`

---

## Files created

Scripts:

- `src/config_global.py`
- `src/01_download_cities_global.py`
- `src/02_generate_patches_global.py`
- `src/03_compute_graph_features_global.py`
- `src/04_compute_building_features_global.py`
- `src/05_compute_terrain_poi_features_global.py`
- `src/06_compute_entropy_global.py`
- `src/07_assemble_dataset_global.py`

Outputs:

- `data/raw_global/*.graphml`
- `data/raw_global/*_srtm.tif`
- `data/processed_global/patch_centres_global_full.csv`
- `data/processed_global/patch_centres.csv`
- `data/processed_global/graph_features.csv`
- `data/processed_global/building_features.csv`
- `data/processed_global/terrain_poi_features.csv`
- `data/processed_global/entropy_features.csv`
- `data/processed_global/dataset_global_assembled.csv`

Backups:

- `data/processed_global/graph_features_directed_backup.csv`
- `data/processed_global/building_features_place_boundary_backup.csv`

---

## Important fixes made

### 1. Tokyo download was too large

Issue:

Tokyo full-place download triggered hundreds of Overpass subqueries.

Fix:

Changed global city downloads to radius-based extraction.

Method:

`ox.graph_from_point()`

Radius:

`5000m`

Reason:

This makes global cities comparable and avoids huge downloads.

---

### 2. Graph features used directed degree

Issue:

First graph run gave:

- `dead_end_ratio = 0`
- `proportion_3way = 0`

This was suspicious.

Likely cause:

OSMnx street graphs are directed.

Fix:

Used undirected graph logic and OSMnx street counts.

Reason:

Street morphology should count physical connections, not travel directions.

---

### 3. Building extraction failed first

Issue:

First building run produced:

`405 zero-building patches / 436`

This was not plausible.

Likely cause:

Street graphs used radius extraction, but buildings used place-boundary extraction.

Fix:

Changed building and open-space extraction to use:

`ox.features_from_point()`

with the same 5000m radius.

Result:

Zero-building patches reduced to:

`21 / 436`

---

### 4. Terrain failed first

Issue:

All terrain values were missing.

Cause:

OpenTopography API key was missing.

Fix:

Added `OPENTOPO_API_KEY` to `.env`.

Result:

Terrain now works.

Missing terrain values:

`0`

---

## Final dataset checkpoint

Output:

`data/processed_global/dataset_global_assembled.csv`

Rows:

`436`

Columns:

`50`

Missing values:

`0`

Bad entropy rows:

`0`

Zero-building patches:

`21`

Zero-POI patches:

`50`

Decision:

Pause extraction here.

Reason:

The global pilot is clean enough for EDA and comparison.

---

## Valid graph patches by city

- Bangkok: 53
- Cairo: 72
- Marrakesh: 41
- Mexico City: 91
- New York: 83
- Tokyo: 96

Total valid graph patches:

`436`

Discarded patches:

`164`

---

## Building feature status

Building extraction is now usable.

City averages:

- Bangkok: medium building coverage
- Cairo: lower coverage, some zero-building patches
- Marrakesh: compact but lower coverage
- Mexico City: medium-high coverage
- New York: high building coverage
- Tokyo: high building count

Known warning:

Cairo has the highest number of zero-building patches.

---

## POI feature status

POI extraction is usable.

Known warning:

`50 zero-POI patches`

Main issue:

Cairo has many zero-POI patches.

Interpretation:

This may reflect OSM POI incompleteness, not real lack of activity.

---

## Terrain feature status

Terrain now works.

Missing terrain values:

`0`

Mean slope by city:

- Bangkok: around 4.42°
- Cairo: around 5.52°
- Marrakesh: around 2.30°
- Mexico City: around 3.11°
- New York: around 4.68°
- Tokyo: around 3.67°

---

## Entropy feature status

Entropy rows:

`436`

Bad entropy rows:

`0`

Entropy range:

- minimum: around 0.18
- maximum: around 0.96

City reading:

- New York: lower entropy, stronger grid
- Mexico City: lower entropy, more directional order
- Tokyo: higher entropy, more directional diversity
- Bangkok: higher entropy, mixed directions
- Cairo: higher entropy, mixed directions
- Marrakesh: higher entropy, organic pattern

---

## Dataset columns added for global comparison

Metadata columns:

- `patch_id`
- `city`
- `code`
- `lat`
- `lon`
- `country`
- `continent`
- `dataset_scope`
- `has_urban_atlas_label`
- `semantic_tag`
- `semantic_tag_confidence`

Default global metadata:

- `dataset_scope = global_comparison`
- `has_urban_atlas_label = false`
- `semantic_tag = unknown`
- `semantic_tag_confidence = unknown`

---

## Current status checklist

- [x] Pulled latest repo
- [x] Created separate global branch
- [x] Created global notes file
- [x] Created `config_global.py`
- [x] Created global data folders
- [x] Added 6 pilot cities
- [x] Downloaded global city graphs
- [x] Generated full global patch centers
- [x] Created balanced 600-patch sample
- [x] Added global metadata columns
- [x] Computed corrected graph features
- [x]