import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.config_global import PROCESSED_DIR


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading feature files...\n")

    # ── load each feature CSV ─────────────────────────────────────

    # graph features — 13 features + metadata
    graph_path = PROCESSED_DIR / "graph_features.csv"
    if not graph_path.exists():
        print("ERROR: graph_features.csv not found")
        print("Run 03_compute_graph_features.py first")
        return
    graph_df = pd.read_csv(graph_path)
    print(f"Graph features:       {len(graph_df)} rows, "
          f"{len(graph_df.columns)} columns")

    # building features — 7 features
    building_path = PROCESSED_DIR / "building_features.csv"
    if not building_path.exists():
        print("ERROR: building_features.csv not found")
        print("Run 04_compute_building_features.py first")
        return
    building_df = pd.read_csv(building_path)
    print(f"Building features:    {len(building_df)} rows, "
          f"{len(building_df.columns)} columns")

    # terrain + POI features — 13 features
    terrain_path = PROCESSED_DIR / "terrain_poi_features.csv"
    if not terrain_path.exists():
        print("ERROR: terrain_poi_features.csv not found")
        print("Run 05_compute_terrain_poi_features.py first")
        return
    terrain_df = pd.read_csv(terrain_path)
    print(f"Terrain+POI features: {len(terrain_df)} rows, "
          f"{len(terrain_df.columns)} columns")

    # ── join all feature sets on patch_id ────────────────────────

    print("\nJoining feature sets on patch_id...")

    # start with graph features as the base
    # it has the most complete set of valid patches
    df = graph_df.copy()

    # define which columns are features vs metadata
    # metadata columns are duplicated across files — drop them
    # when merging
    meta_cols = ['patch_id', 'city', 'code', 'lat', 'lon']

    # join building features
    building_feat_cols = [c for c in building_df.columns
                          if c not in meta_cols]
    df = df.merge(
        building_df[['patch_id'] + building_feat_cols],
        on='patch_id',
        how='left'
    )

    # join terrain and POI features
    terrain_feat_cols = [c for c in terrain_df.columns
                         if c not in meta_cols]
    df = df.merge(
        terrain_df[['patch_id'] + terrain_feat_cols],
        on='patch_id',
        how='left'
    )

    print(f"Joined dataset: {len(df)} rows, "
          f"{len(df.columns)} columns")

    # ── compute entropy ───────────────────────────────────────────
    # entropy is computed here from the graph features
    # rather than in a separate script since we already have
    # the bearings cached in the graph files
    # we load it from a separate entropy CSV if it exists
    # otherwise we note it needs to be computed

    entropy_path = PROCESSED_DIR / "entropy_features.csv"
    if entropy_path.exists():
        entropy_df = pd.read_csv(entropy_path)
        print(f"Entropy features:     {len(entropy_df)} rows")
        entropy_feat_cols = [c for c in entropy_df.columns
                             if c not in meta_cols]
        df = df.merge(
            entropy_df[['patch_id'] + entropy_feat_cols],
            on='patch_id',
            how='left'
        )
    else:
        print("NOTE: entropy_features.csv not found")
        print("      Run 06_compute_entropy.py to add entropy")
        print("      Assembling without entropy for now")

    # ── quality checks ────────────────────────────────────────────

    print("\nRunning quality checks...")

    initial_count = len(df)

    # check for completely empty rows
    df = df.dropna(how='all')

    # report missing values per column
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        print("\nMissing values per column:")
        print(missing.to_string())
    else:
        print("No missing values found")

    # check entropy range if present
    if 'entropy_normalised' in df.columns:
        invalid_entropy = df[
            (df['entropy_normalised'] < 0) |
            (df['entropy_normalised'] > 1)
        ]
        if len(invalid_entropy) > 0:
            print(f"WARNING: {len(invalid_entropy)} patches "
                  f"with entropy outside 0-1 range — removing")
            df = df[
                (df['entropy_normalised'] >= 0) &
                (df['entropy_normalised'] <= 1)
            ]

    print(f"\nFinal dataset: {len(df)} rows "
          f"(removed {initial_count - len(df)} rows)")

    # ── print column summary ──────────────────────────────────────

    print("\nColumn summary:")
    print(f"  Metadata:          "
          f"{[c for c in meta_cols if c in df.columns]}")

    graph_cols = [c for c in df.columns if c in [
        'n_nodes', 'n_edges', 'mean_node_degree', 'dead_end_ratio',
        'proportion_3way', 'proportion_4way', 'intersection_density',
        'mean_edge_length', 'std_edge_length', 'cv_edge_length',
        'total_edge_length', 'network_density', 'grain_ratio',
        'meshedness', 'beta_index'
    ]]
    print(f"  Graph features:    {len(graph_cols)} columns")

    building_cols = [c for c in df.columns if c in [
        'building_count', 'pct_apartments', 'pct_houses',
        'pct_commercial', 'pct_other', 'building_coverage'
    ]]
    print(f"  Building features: {len(building_cols)} columns")

    terrain_cols = [c for c in df.columns if c in [
        'mean_slope_deg', 'max_slope_deg', 'elevation_variance'
    ]]
    print(f"  Terrain features:  {len(terrain_cols)} columns")

    poi_cols = [c for c in df.columns if c in [
        'poi_count', 'poi_density', 'functional_entropy',
        'n_poi_categories', 'pct_food_drink', 'pct_retail',
        'pct_civic', 'pct_culture', 'pct_transport', 'pct_services'
    ]]
    print(f"  POI features:      {len(poi_cols)} columns")

    if 'entropy_normalised' in df.columns:
        print(f"  Entropy:           1 column (target input feature)")

    # ── save ──────────────────────────────────────────────────────

    output_path = PROCESSED_DIR / "dataset_assembled.csv"
    df.to_csv(output_path, index=False)

    print(f"\nSaved to {output_path}")
    print(f"Total features: {len(df.columns) - len(meta_cols)} "
          f"input columns + metadata")
    print("\nDataset head:")
    print(df[meta_cols + graph_cols[:3]].head())


if __name__ == "__main__":
    main()