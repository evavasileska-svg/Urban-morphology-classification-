# Global City Pilot Notes

## Goal

Test extra OpenStreetMap data from African, Asian, and American cities.

This is a separate comparison dataset.

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

Use separate global filenames instead.

---

## New global files to create

Planned files:

- `src/config_global.py`
- `data/raw_global/`
- `data/processed_global/`
- `data/processed_global/patch_centres_global.csv`
- `data/processed_global/graph_features_global.csv`
- `data/processed_global/building_features_global.csv`
- `data/processed_global/terrain_poi_features_global.csv`
- `data/processed_global/entropy_features_global.csv`
- `data/processed_global/dataset_global_assembled.csv`

---

## Dataset logic

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

Start small before scaling.

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

Maximum pilot patches per city:

`100`

Reason:

Avoid one large city dominating the dataset.

---

## Columns to add later

Useful metadata columns:

- `patch_id`
- `city`
- `country`
- `continent`
- `lat`
- `lon`
- `dataset_scope`
- `has_urban_atlas_label`
- `semantic_tag`
- `semantic_tag_confidence`

Default values for global patches:

- `dataset_scope = global_comparison`
- `has_urban_atlas_label = false`
- `semantic_tag = unknown`
- `semantic_tag_confidence = unknown`

---

## First pipeline steps

Step 1:

Create `config_global.py`.

Step 2:

Download global city street graphs.

Step 3:

Generate global patch centers.

Step 4:

Limit patches per city.

Step 5:

Compute graph features only.

Step 6:

Check valid and discarded patches.

Step 7:

Only then compute buildings, POIs, terrain, and entropy.

---

## Quality checks

For each city, check:

- number of generated patches
- number of valid graph patches
- number of discarded patches
- average intersection density
- average dead-end ratio
- average building count
- number of patches with zero buildings
- average POI count
- missing terrain values

---

## Risks

Risk:

Global cities overwrite team CSVs.

Fix:

Use `_global` filenames.

Risk:

Global cities get mixed with Urban Atlas labels.

Fix:

Use `has_urban_atlas_label = false`.

Risk:

Large cities dominate the dataset.

Fix:

Limit patch count per city.

Risk:

OSM data is incomplete.

Fix:

Add quality columns and report missing data.

---

## Team message

Message sent to team:

“I’m testing extra OSM data from African, Asian, and American cities. I’ll keep this separate from the main European Urban Atlas dataset. I’m working on a separate branch called `eduardo-global-osm-cities`, and I’ll save outputs with `_global` names so I don’t overwrite shared files.”

---

## Current status

- [ ] Pulled latest repo
- [ ] Created branch
- [ ] Created notes file
- [ ] Created `config_global.py`
- [ ] Created global data folders
- [ ] Added pilot cities
- [ ] Downloaded global city graphs
- [ ] Generated global patch centers
- [ ] Computed graph features
- [ ] Checked patch quality
- [ ] Reported results to team

---

## Notes

Write problems, decisions, and changes here.

Date:

Decision:

Reason:

Next action: