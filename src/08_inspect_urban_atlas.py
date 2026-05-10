import geopandas as gpd
from pathlib import Path

UA_PATH = Path("data/urban_atlas/urban_atlas.gpkg")

def main():
    if not UA_PATH.exists():
        raise FileNotFoundError(f"Urban Atlas file not found: {UA_PATH}")

    ua = gpd.read_file(UA_PATH)

    print("Rows:", len(ua))
    print("CRS:", ua.crs)
    print("Columns:")
    print(ua.columns.tolist())

    print("\nFirst rows:")
    print(ua.head())

    print("\nGeometry types:")
    print(ua.geometry.geom_type.value_counts())

if __name__ == "__main__":
    main()