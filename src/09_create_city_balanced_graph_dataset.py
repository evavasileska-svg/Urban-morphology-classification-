import pandas as pd
from pathlib import Path
import sys

# Add repo root to path.
sys.path.append(str(Path(__file__).parent.parent))

from src.config_global import PROCESSED_DIR


def main():
    input_path = PROCESSED_DIR / "graph_features.csv"
    output_path = PROCESSED_DIR / "graph_features_city_balanced.csv"

    # Load graph features.
    df = pd.read_csv(input_path)

    # Check city counts.
    counts = df["code"].value_counts().sort_index()
    print("Original valid patch counts by city:")
    print(counts)
    print()

    # Use the smallest city count as the balanced sample size.
    n_per_city = counts.min()
    print(f"Balancing to {n_per_city} patches per city.")
    print()

    # Sample the same number of patches per city.
    balanced = (
        df.groupby("code", group_keys=False)
        .sample(n=n_per_city, random_state=42)
        .reset_index(drop=True)
    )

    # Check balanced counts.
    balanced_counts = balanced["code"].value_counts().sort_index()
    print("Balanced patch counts by city:")
    print(balanced_counts)
    print()

    # Save output.
    balanced.to_csv(output_path, index=False)

    print(f"Saved balanced dataset to: {output_path}")
    print(f"Total rows: {len(balanced)}")


if __name__ == "__main__":
    main()