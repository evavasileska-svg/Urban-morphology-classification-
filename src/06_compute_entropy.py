import osmnx as ox
import numpy as np
import pandas as pd
from pathlib import Path
from math import cos, radians
from tqdm import tqdm
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.config import (CITIES, RAW_DIR, PROCESSED_DIR,
                         PATCH_SIZE_M, N_BEARING_BINS)


def get_patch_subgraph(G, centre_lat, centre_lon, patch_size_m):
    """Clip city graph to a square patch around a centre point."""
    delta_lat = (patch_size_m / 2) / 111000
    delta_lon = (patch_size_m / 2) / (
        111000 * cos(radians(centre_lat))
    )

    north = centre_lat + delta_lat
    south = centre_lat - delta_lat
    east  = centre_lon + delta_lon
    west  = centre_lon - delta_lon

    nodes_in_bbox = [
        node for node, data in G.nodes(data=True)
        if south <= data['y'] <= north
        and west  <= data['x'] <= east
    ]

    if not nodes_in_bbox:
        return None

    return G.subgraph(nodes_in_bbox).copy()


def compute_entropy(G, num_bins=36):
    """
    Compute Shannon entropy of street bearing distribution.
    Follows Boeing (2019) exactly.
    """
    bearings_list = []
    lengths_list  = []

    for u, v, data in G.edges(data=True):
        b = data.get('bearing', None)
        l = data.get('length', None)
        if b is not None and l is not None and l > 0:
            # add bearing and its reciprocal
            b_reciprocal = (b + 180) % 360
            bearings_list.append(b)
            bearings_list.append(b_reciprocal)
            lengths_list.append(l)
            lengths_list.append(l)

    if len(bearings_list) < 10:
        return None

    bearings = np.array(bearings_list)
    lengths  = np.array(lengths_list)

    # Boeing: 36 bins of 10 degrees, shifted by -5
    # so bin edges are at -5, 5, 15 ... 355, 365
    # bearings between 355 and 360 wrap into first bin
    # apply shift: subtract 5 then mod 360
    bearings_shifted = (bearings - 5) % 360

    # now bin from 0 to 360 in 36 equal bins
    bin_edges = np.linspace(0, 360, num_bins + 1)

    # ── unweighted Ho ────────────────────────────────────────────
    counts_uw, _ = np.histogram(bearings_shifted, bins=bin_edges)
    total_uw = counts_uw.sum()
    if total_uw == 0:
        return None
    prop_uw = counts_uw / total_uw
    prop_uw_nz = prop_uw[prop_uw > 0]
    Ho = -np.sum(prop_uw_nz * np.log(prop_uw_nz))

    # ── weighted Hw ──────────────────────────────────────────────
    counts_w, _ = np.histogram(
        bearings_shifted, bins=bin_edges, weights=lengths
    )
    total_w = counts_w.sum()
    if total_w == 0:
        return None
    prop_w = counts_w / total_w
    prop_w_nz = prop_w[prop_w > 0]
    Hw = -np.sum(prop_w_nz * np.log(prop_w_nz))

    # ── normalise ────────────────────────────────────────────────
    H_max         = np.log(num_bins)   # 3.584 nats
    Ho_normalised = Ho / H_max
    Hw_normalised = Hw / H_max

    # ── orientation-order phi (Boeing eq. 3) ─────────────────────
    Hg  = np.log(4)   # 1.386 nats — perfect four-way grid
    phi = 1 - ((Ho - Hg) / (H_max - Hg)) ** 2
    phi = float(max(0.0, min(1.0, phi)))

    # ── additional descriptors ───────────────────────────────────
    dominant_bin     = int(np.argmax(counts_uw))
    dominant_bearing = (dominant_bin * 10 + 5) % 360
    n_dominant_peaks = int((prop_uw > 0.05).sum())

    return {
        'entropy_raw':           round(Ho, 6),
        'entropy_normalised':    round(Ho_normalised, 6),
        'entropy_weighted_raw':  round(Hw, 6),
        'entropy_weighted_norm': round(Hw_normalised, 6),
        'orientation_order_phi': round(phi, 6),
        'dominant_bearing':      round(float(dominant_bearing), 2),
        'n_dominant_peaks':      n_dominant_peaks,
    }

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # load valid patches
    graph_path = PROCESSED_DIR / "graph_features.csv"
    if not graph_path.exists():
        print("graph_features.csv not found")
        print("Run 03_compute_graph_features.py first")
        return

    patches = pd.read_csv(graph_path)
    print(f"Loaded {len(patches)} valid patches\n")

    # load existing results if they exist
    output_path = PROCESSED_DIR / "entropy_features.csv"
    if output_path.exists():
        existing = pd.read_csv(output_path)
        existing_ids = set(existing['patch_id'].values)
        print(f"Found {len(existing)} existing — skipping")
        all_rows = existing.to_dict('records')
    else:
        existing_ids = set()
        all_rows = []

    discarded = 0

    for city in CITIES:
        city_patches = patches[patches['code'] == city['code']]

        # skip already computed patches
        city_patches = city_patches[
            ~city_patches['patch_id'].isin(existing_ids)
        ]

        if len(city_patches) == 0:
            print(f"{city['name']} — already done, skipping")
            continue

        print(f"Processing {city['name']} "
              f"— {len(city_patches)} patches...")

        # load cached city graph
        graph_file = RAW_DIR / f"{city['code']}.graphml"
        if not graph_file.exists():
            print(f"  graph not found — skipping")
            continue

        G = ox.load_graphml(graph_file)

        # verify bearings are present
        sample_edge = next(iter(G.edges(data=True)), None)
        if sample_edge and 'bearing' not in sample_edge[2]:
            print(f"  bearings missing — adding now...")
            G = ox.bearing.add_edge_bearings(G)

        city_valid     = 0
        city_discarded = 0

        for _, row in tqdm(city_patches.iterrows(),
                           total=len(city_patches),
                           desc=f"  {city['code']}"):

            G_patch = get_patch_subgraph(
                G, row['lat'], row['lon'], PATCH_SIZE_M
            )

            if G_patch is None:
                city_discarded += 1
                discarded += 1
                continue

            entropy_feats = compute_entropy(
                G_patch, num_bins=N_BEARING_BINS
            )

            if entropy_feats is None:
                city_discarded += 1
                discarded += 1
                continue

            result = {
                'patch_id': row['patch_id'],
                'city':     row['city'],
                'code':     row['code'],
                'lat':      row['lat'],
                'lon':      row['lon'],
            }
            result.update(entropy_feats)
            all_rows.append(result)
            city_valid += 1

        print(f"  valid: {city_valid} · "
              f"discarded: {city_discarded}\n")

        # save after each city
        df = pd.DataFrame(all_rows)
        df.to_csv(output_path, index=False)
        print(f"  progress saved — {len(df)} total patches so far")

    # final save
    df = pd.DataFrame(all_rows)
    df.to_csv(output_path, index=False)

    print(f"\nTotal valid: {len(df)}")
    print(f"Total discarded: {discarded}")
    print(f"Saved to {output_path}")
    print("\nEntropy distribution:")
    print(df['entropy_normalised'].describe())


if __name__ == "__main__":
    main()

# export entropy-only CSV — clean standalone output
    entropy_cols = [
        'patch_id', 'city', 'code', 'lat', 'lon',
        'entropy_raw',
        'entropy_normalised',
        'entropy_weighted_raw',
        'entropy_weighted_norm',
        'orientation_order_phi',
        'dominant_bearing',
        'n_dominant_peaks',
    ]

    # keep only columns that exist in the dataframe
    entropy_cols_present = [c for c in entropy_cols 
                            if c in df.columns]

    entropy_export = df[entropy_cols_present].copy()
    entropy_export_path = PROCESSED_DIR / "entropy_boeing.csv"
    entropy_export.to_csv(entropy_export_path, index=False)

    print(f"\nEntropy-only CSV saved to {entropy_export_path}")
    print(f"Columns: {entropy_cols_present}")
    print(f"Rows: {len(entropy_export)}")

