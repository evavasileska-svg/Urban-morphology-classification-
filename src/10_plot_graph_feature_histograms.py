import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add repo root to path.
sys.path.append(str(Path(__file__).parent.parent))

from src.config_global import PROCESSED_DIR


def main():
    input_path = PROCESSED_DIR / "graph_features_city_balanced.csv"
    output_dir = PROCESSED_DIR / "eda_graph_histograms"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)

    graph_features = [
        "dead_end_ratio",
        "proportion_3way",
        "proportion_4way",
        "intersection_density",
        "network_density",
        "meshedness",
        "beta_index",
        "mean_node_degree",
        "mean_edge_length",
        "cv_edge_length",
    ]

    for feature in graph_features:
        plt.figure(figsize=(8, 5))
        plt.hist(df[feature].dropna(), bins=40)
        plt.title(f"Distribution of {feature}")
        plt.xlabel(feature)
        plt.ylabel("Number of patches")
        plt.tight_layout()

        output_path = output_dir / f"{feature}_histogram.png"
        plt.savefig(output_path, dpi=200)
        plt.close()

        print(f"Saved: {output_path}")

    print("\nDone. Histograms saved.")
    print(f"Output folder: {output_dir}")


if __name__ == "__main__":
    main()