import osmnx as ox
import networkx as nx
import numpy as np
import pandas as pd
from pathlib import Path
from math import cos, radians
from tqdm import tqdm
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.config import (CITIES, RAW_DIR, PROCESSED_DIR,
                         PATCH_SIZE_M, MIN_SEGMENTS)


def get_patch_subgraph(G, centre_lat, centre_lon, patch_size_m):
    """Clip city graph to a square patch around a centre point."""

    delta_lat = (patch_size_m / 2) / 111000
    delta_lon = (patch_size_m / 2) / (111000 * cos(radians(centre_lat)))

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


def is_valid_patch(G):
    """Check patch has enough data for reliable computation."""
    if G is None:
        return False
    if G.number_of_edges() < MIN_SEGMENTS:
        return False
    if G.number_of_nodes() < 10:
        return False
    # largest connected component must be 85% of nodes
    largest_cc = max(nx.weakly_connected_components(G), key=len)
    if len(largest_cc) / G.number_of_nodes() < 0.85:
        return False
    return True


def compute_graph_metrics(G, patch_size_m):
    """Compute all graph metric features from the subgraph."""

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()

    # node degree features
    degrees = [d for _, d in G.degree()]

    mean_node_degree   = np.mean(degrees)
    dead_end_ratio     = sum(1 for d in degrees if d == 1) / n_nodes
    proportion_3way    = sum(1 for d in degrees if d == 3) / n_nodes
    proportion_4way    = sum(1 for d in degrees if d == 4) / n_nodes

    # patch area in km²
    patch_area_km2 = (patch_size_m / 1000) ** 2

    intersection_density = n_nodes / patch_area_km2

    # edge length features
    edge_lengths = [
        data.get('length', 0)
        for _, _, data in G.edges(data=True)
    ]
    edge_lengths = [l for l in edge_lengths if l > 0]

    if not edge_lengths:
        return None

    mean_edge_length  = np.mean(edge_lengths)
    std_edge_length   = np.std(edge_lengths)
    cv_edge_length    = std_edge_length / mean_edge_length \
                        if mean_edge_length > 0 else 0
    total_edge_length = np.sum(edge_lengths)
    network_density   = (total_edge_length / 1000) / patch_area_km2

    # derived proportions
    grain_ratio = mean_node_degree / mean_edge_length \
                  if mean_edge_length > 0 else 0

    meshedness = (n_edges - n_nodes + 1) / (2 * n_nodes - 5) \
                 if n_nodes > 3 else 0
    meshedness = max(0, min(1, meshedness))

    beta_index = n_edges / n_nodes if n_nodes > 0 else 0

    return {
        'n_nodes':               n_nodes,
        'n_edges':               n_edges,
        'mean_node_degree':      round(mean_node_degree, 4),
        'dead_end_ratio':        round(dead_end_ratio, 4),
        'proportion_3way':       round(proportion_3way, 4),
        'proportion_4way':       round(proportion_4way, 4),
        'intersection_density':  round(intersection_density, 2),
        'mean_edge_length':      round(mean_edge_length, 2),
        'std_edge_length':       round(std_edge_length, 2),
        'cv_edge_length':        round(cv_edge_length, 4),
        'total_edge_length':     round(total_edge_length, 2),
        'network_density':       round(network_density, 4),
        'grain_ratio':           round(grain_ratio, 6),
        'meshedness':            round(meshedness, 4),
        'beta_index':            round(beta_index, 4),
    }


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # load all patch centres
    centres_path = PROCESSED_DIR / "patch_centres.csv"
    centres = pd.read_csv(centres_path)
    print(f"Loaded {len(centres)} patch centres\n")

    # load existing results if they exist
    # skip patches already computed
    output_path = PROCESSED_DIR / "graph_features.csv"
    if output_path.exists():
        existing = pd.read_csv(output_path)
        existing_ids = set(existing['patch_id'].values)
        print(f"Found {len(existing)} existing patches — skipping")
        all_rows = existing.to_dict('records')
    else:
        existing_ids = set()
        all_rows = []

    discarded = 0

    # process city by city
    for city in CITIES:
        city_patches = centres[centres['code'] == city['code']]

        # skip patches already computed
        city_patches = city_patches[
            ~city_patches['patch_id'].isin(existing_ids)
        ]

        if len(city_patches) == 0:
            print(f"{city['name']} — already done, skipping")
            continue

        print(f"Processing {city['name']} "
              f"— {len(city_patches)} new centres...")

        # load cached city graph once per city
        graph_path = RAW_DIR / f"{city['code']}.graphml"
        if not graph_path.exists():
            print(f"  graph not found — skipping")
            continue

        G = ox.load_graphml(graph_path)

        city_valid     = 0
        city_discarded = 0

        for _, row in tqdm(city_patches.iterrows(),
                           total=len(city_patches),
                           desc=f"  {city['code']}"):

            G_patch = get_patch_subgraph(
                G, row['lat'], row['lon'], PATCH_SIZE_M
            )

            if not is_valid_patch(G_patch):
                city_discarded += 1
                discarded += 1
                continue

            metrics = compute_graph_metrics(G_patch, PATCH_SIZE_M)
            if metrics is None:
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
            result.update(metrics)
            all_rows.append(result)
            city_valid += 1

        print(f"  valid: {city_valid} · "
              f"discarded: {city_discarded}\n")

        # save after each city in case of interruption
        df = pd.DataFrame(all_rows)
        df.to_csv(output_path, index=False)
        print(f"  progress saved — {len(df)} total patches so far")

    # final save
    df = pd.DataFrame(all_rows)
    df.to_csv(output_path, index=False)

    print(f"\nTotal valid patches: {len(df)}")
    print(f"Total discarded:     {discarded}")
    print(f"Saved to {output_path}")

    # save results
    df = pd.DataFrame(all_rows)
    output_path = PROCESSED_DIR / "graph_features.csv"
    df.to_csv(output_path, index=False)

    print(f"Total valid patches: {len(df)}")
    print(f"Total discarded:     {discarded}")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()