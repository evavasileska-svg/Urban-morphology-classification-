import osmnx as ox
import numpy as np
import pandas as pd
from pathlib import Path
from math import cos, radians
from tqdm import tqdm
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.config_global import (
    CITIES,
    RAW_DIR,
    PROCESSED_DIR,
    PATCH_SIZE_M,
    N_BEARING_BINS
)


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
    Follows Boeing (2019):
    - undirected bearings (% 180)
    - minus 5 degree bin shift
    - length weighted histogram
    - normalised by log(num_bins)
    """
    bearings = []
    lengths  = []

    for u, v, data in G.edges(data=True):
        b = data.get('bearing', None)
        l = data.get('length', None)
        if b is not None and l is not None and l > 0:
            bearings.append(b)
            lengths.append(l)

    if len(bearings) < 10:
        return None

    bearings = np.array(bearings)
    lengths  = np.array(lengths)

    # step 1 — collapse to undirected 0 to 180
    bearings_undirected = bearings % 180

    # step 2 — Boeing minus 5 degree shift
    # prevents streets at 0 and 90 degrees sitting on bin edges
    bearings_shifted = (bearings_undirected - 5) % 180

    # step 3 — length weighted histogram
    bin_edges = np.linspace(0, 180, num_bins + 1)
    counts, _ = np.histogram(
        bearings_shifted,
        bins=bin_edges,
        weights=lengths
    )

    # step 4 — proportions
    total = counts.sum()
    if total == 0:
        return None
    proportions = counts / total

    # step 5 — Shannon entropy
    proportions_nz = proportions[proportions > 0]
    H = -np.sum(proportions_nz * np.log(proportions_nz))

    # step 6 — normalise to 0-1
    H_max        = np.log(num_bins)
    H_normalised = H / H_max

    # also store the dominant bearing — direction most streets point
    dominant_bin  = np.argmax(counts)
    dominant_bearing = bin_edges[dominant_bin] + 5  # undo shift

    # number of bins with more than 5% of streets
    # low number = strong dominant direction (grid)
    # high number = many directions (organic)
    n_dominant_peaks = int((proportions > 0.05).sum())

    return {
        'entropy_raw':        round(H, 6),
        'entropy_normalised': round(H_normalised, 6),
        'dominant_bearing':   round(dominant_bearing, 2),
        'n_dominant_peaks':   n_dominant_peaks,
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

