"""
generate_eda_dataset.py
-----------------------
Generates data/processed/dataset_city_balanced_eda.csv

Processes only the 8 original cities, sampling up to SAMPLE_PER_CITY
patch centres per city so the script completes in reasonable time.
Each city contributes TARGET_PER_CITY rows in the final CSV.

Run from the repo root:
    python src/generate_eda_dataset.py
"""

import osmnx as ox
import networkx as nx
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from pathlib import Path
from math import cos, radians, log
from tqdm import tqdm
import sys
import warnings
warnings.filterwarnings("ignore")

sys.path.append(str(Path(__file__).parent.parent))
from src.config import RAW_DIR, PROCESSED_DIR, PATCH_SIZE_M, MIN_SEGMENTS

# ── settings ──────────────────────────────────────────────────────────────────

EIGHT_CITIES = [
    {"name": "Vienna, Austria",                   "code": "vienna",     "lat": 48.2082, "lon": 16.3738},
    {"name": "Prague, Czech Republic",             "code": "prague",     "lat": 50.0755, "lon": 14.4378},
    {"name": "Barcelona, Spain",                   "code": "barcelona",  "lat": 41.3851, "lon":  2.1734},
    {"name": "Amsterdam, Netherlands",             "code": "amsterdam",  "lat": 52.3676, "lon":  4.9041},
    {"name": "Sarajevo, Bosnia and Herzegovina",   "code": "sarajevo",   "lat": 43.8563, "lon": 18.4131},
    {"name": "Warsaw, Poland",                     "code": "warsaw",     "lat": 52.2297, "lon": 21.0122},
    {"name": "Skopje, North Macedonia",            "code": "skopje",     "lat": 41.9973, "lon": 21.4280},
    {"name": "Riga, Latvia",                       "code": "riga",       "lat": 56.9460, "lon": 24.1059},
]

SAMPLE_PER_CITY = 800   # patch centres to attempt per city
TARGET_PER_CITY = 250   # valid patches to keep per city
N_BEARING_BINS  = 36
SEED            = 42

# ── geometry helpers ───────────────────────────────────────────────────────────

def get_patch_polygon(lat, lon, size_m=PATCH_SIZE_M):
    dlat = (size_m / 2) / 111000
    dlon = (size_m / 2) / (111000 * cos(radians(lat)))
    return box(lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def get_patch_subgraph(G, lat, lon, size_m=PATCH_SIZE_M):
    dlat = (size_m / 2) / 111000
    dlon = (size_m / 2) / (111000 * cos(radians(lat)))
    nodes = [n for n, d in G.nodes(data=True)
             if lat - dlat <= d["y"] <= lat + dlat
             and lon - dlon <= d["x"] <= lon + dlon]
    return G.subgraph(nodes).copy() if nodes else None


def is_valid_patch(G):
    if G is None or G.number_of_edges() < MIN_SEGMENTS:
        return False
    if G.number_of_nodes() < 10:
        return False
    largest_cc = max(nx.weakly_connected_components(G), key=len)
    return len(largest_cc) / G.number_of_nodes() >= 0.85

# ── feature computers ──────────────────────────────────────────────────────────

def compute_graph_metrics(G, size_m=PATCH_SIZE_M):
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    degrees = [d for _, d in G.degree()]
    area_km2 = (size_m / 1000) ** 2

    edge_lengths = [d.get("length", 0) for _, _, d in G.edges(data=True) if d.get("length", 0) > 0]
    if not edge_lengths:
        return None

    mel  = float(np.mean(edge_lengths))
    sel  = float(np.std(edge_lengths))
    tel  = float(np.sum(edge_lengths))

    return {
        "n_nodes":              n_nodes,
        "n_edges":              n_edges,
        "mean_node_degree":     round(float(np.mean(degrees)), 4),
        "dead_end_ratio":       round(sum(1 for d in degrees if d == 1) / n_nodes, 4),
        "proportion_3way":      round(sum(1 for d in degrees if d == 3) / n_nodes, 4),
        "proportion_4way":      round(sum(1 for d in degrees if d == 4) / n_nodes, 4),
        "intersection_density": round(n_nodes / area_km2, 2),
        "mean_edge_length":     round(mel, 2),
        "std_edge_length":      round(sel, 2),
        "cv_edge_length":       round(sel / mel if mel > 0 else 0, 4),
        "total_edge_length":    round(tel, 2),
        "network_density":      round((tel / 1000) / area_km2, 4),
        "grain_ratio":          round(float(np.mean(degrees)) / mel if mel > 0 else 0, 6),
        "meshedness":           round(max(0, min(1, (n_edges - n_nodes + 1) / (2 * n_nodes - 5))) if n_nodes > 3 else 0, 4),
        "beta_index":           round(n_edges / n_nodes if n_nodes > 0 else 0, 4),
    }


def compute_entropy(G, num_bins=N_BEARING_BINS):
    bearings, lengths = [], []
    for u, v, data in G.edges(data=True):
        b = data.get("bearing")
        l = data.get("length")
        if b is not None and l and l > 0:
            bearings += [b, (b + 180) % 360]
            lengths  += [l, l]

    if len(bearings) < 10:
        return None

    ba = np.array(bearings)
    la = np.array(lengths)
    shifted = (ba - 5) % 360
    edges   = np.linspace(0, 360, num_bins + 1)

    cu, _ = np.histogram(shifted, bins=edges)
    pu    = cu / cu.sum() if cu.sum() > 0 else cu
    Ho    = -np.sum(pu[pu > 0] * np.log(pu[pu > 0]))

    cw, _ = np.histogram(shifted, bins=edges, weights=la)
    pw    = cw / cw.sum() if cw.sum() > 0 else cw
    Hw    = -np.sum(pw[pw > 0] * np.log(pw[pw > 0]))

    H_max = log(num_bins)
    Hg    = log(4)
    phi   = float(max(0.0, min(1.0, 1 - ((Ho - Hg) / (H_max - Hg)) ** 2)))

    return {
        "entropy_raw":           round(Ho, 6),
        "entropy_normalised":    round(Ho / H_max, 6),
        "entropy_weighted_raw":  round(Hw, 6),
        "entropy_weighted_norm": round(Hw / H_max, 6),
        "orientation_order_phi": round(phi, 6),
    }


def compute_building_features(buildings_gdf, open_space_gdf, patch_poly):
    area_m2 = PATCH_SIZE_M ** 2
    empty = {"building_count": 0, "pct_apartments": 0.0, "pct_houses": 0.0,
             "pct_commercial": 0.0, "pct_other": 0.0,
             "building_coverage": 0.0, "public_space_ratio": 0.0}

    # buildings
    if buildings_gdf is not None and len(buildings_gdf) > 0:
        try:
            clip = buildings_gdf[buildings_gdf.geometry.intersects(patch_poly)].copy()
            total = len(clip)
            if total > 0:
                btypes = clip["building"].fillna("yes").str.lower() if "building" in clip.columns else pd.Series(["yes"] * total)
                apt   = btypes.isin(["apartments","apartment","residential","block","flat"]).sum()
                house = btypes.isin(["house","detached","semidetached_house","terrace","bungalow"]).sum()
                comm  = btypes.isin(["commercial","retail","office","supermarket","shop"]).sum()
                try:
                    cp = clip.to_crs("EPSG:3857")
                    cov = min(cp.geometry.area.sum() / area_m2, 1.0)
                except Exception:
                    cov = 0.0
                empty.update({
                    "building_count":    total,
                    "pct_apartments":    round(apt / total, 4),
                    "pct_houses":        round(house / total, 4),
                    "pct_commercial":    round(comm / total, 4),
                    "pct_other":         round(1 - apt/total - house/total - comm/total, 4),
                    "building_coverage": round(cov, 4),
                })
        except Exception:
            pass

    # public space
    if open_space_gdf is not None and len(open_space_gdf) > 0:
        try:
            clip_os = open_space_gdf[open_space_gdf.geometry.intersects(patch_poly)].copy()
            if len(clip_os) > 0:
                cp_os    = clip_os.to_crs("EPSG:3857")
                patch_gs = gpd.GeoSeries([patch_poly], crs="EPSG:4326").to_crs("EPSG:3857").iloc[0]
                total_os = cp_os.geometry.apply(lambda g: g.intersection(patch_gs).area).sum()
                empty["public_space_ratio"] = round(min(total_os / area_m2, 1.0), 4)
        except Exception:
            pass

    return empty

# ── city-level OSM downloads ───────────────────────────────────────────────────

def download_buildings(city_name):
    print(f"  downloading buildings for {city_name}...")
    try:
        gdf = ox.features_from_place(city_name, tags={"building": True})
        gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        print(f"    {len(gdf)} building polygons")
        return gdf
    except Exception as e:
        print(f"    buildings failed: {e}")
        return None


def download_open_space(city_name):
    print(f"  downloading open space for {city_name}...")
    parts = []
    for tags in [{"leisure": "park"}, {"landuse": "grass"}, {"highway": "pedestrian"}]:
        try:
            gdf = ox.features_from_place(city_name, tags=tags)
            gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
            parts.append(gdf)
        except Exception:
            pass
    if parts:
        combined = pd.concat(parts, ignore_index=True)
        print(f"    {len(combined)} open-space polygons")
        return combined
    return None

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    centres_path = PROCESSED_DIR / "patch_centres.csv"
    if not centres_path.exists():
        print("patch_centres.csv not found — run 02_generate_patches.py first")
        sys.exit(1)

    centres_all = pd.read_csv(centres_path)
    rng = np.random.default_rng(SEED)

    all_rows = []

    for city in EIGHT_CITIES:
        code = city["code"]
        name = city["name"]
        print(f"\n{'='*60}")
        print(f"Processing {name}  [{code}]")
        print(f"{'='*60}")

        graph_path = RAW_DIR / f"{code}.graphml"
        if not graph_path.exists():
            print(f"  graphml not found — skipping")
            continue

        # sample centres for this city
        city_centres = centres_all[centres_all["code"] == code].copy()
        if len(city_centres) == 0:
            print(f"  no patch centres — skipping")
            continue

        n_sample = min(SAMPLE_PER_CITY, len(city_centres))
        idx      = rng.choice(len(city_centres), size=n_sample, replace=False)
        sample   = city_centres.iloc[idx].reset_index(drop=True)

        print(f"  sampled {n_sample} centres from {len(city_centres)} available")

        # load graph once
        print(f"  loading graph...")
        G = ox.load_graphml(graph_path)

        # download city-level OSM data once
        buildings  = download_buildings(name)
        open_space = download_open_space(name)

        city_rows = []
        print(f"  computing patch features...")

        for _, row in tqdm(sample.iterrows(), total=len(sample), desc=f"  {code}"):
            lat, lon = row["lat"], row["lon"]

            # graph subgraph
            G_patch = get_patch_subgraph(G, lat, lon)
            if not is_valid_patch(G_patch):
                continue

            # add bearings for entropy
            G_patch = ox.bearing.add_edge_bearings(G_patch)

            # graph metrics
            gm = compute_graph_metrics(G_patch)
            if gm is None:
                continue

            # entropy
            ent = compute_entropy(G_patch)
            if ent is None:
                continue

            # building + open-space features
            patch_poly = get_patch_polygon(lat, lon)
            bf = compute_building_features(buildings, open_space, patch_poly)

            record = {
                "patch_id": row["patch_id"],
                "city":     name,
                "code":     code,
                "lat":      lat,
                "lon":      lon,
            }
            record.update(gm)
            record.update(ent)
            record.update(bf)
            city_rows.append(record)

            # stop once we have enough
            if len(city_rows) >= TARGET_PER_CITY:
                break

        print(f"  valid patches: {len(city_rows)}")
        all_rows.extend(city_rows)

    # ── assemble ───────────────────────────────────────────────────────────────

    df = pd.DataFrame(all_rows)
    print(f"\n{'='*60}")
    print(f"Total rows: {len(df)}")
    print(f"Cities:     {sorted(df['code'].unique().tolist())}")
    print(f"{'='*60}")

    output_path = PROCESSED_DIR / "dataset_city_balanced_eda.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")
    print(f"Rows: {len(df)}  |  Columns: {len(df.columns)}")
    print(df[["code", "patch_id"]].groupby("code").count().rename(columns={"patch_id": "patches"}))


if __name__ == "__main__":
    main()
