import osmnx as ox
import numpy as np
import pandas as pd
from pathlib import Path
from math import cos, radians
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.config_global import CITIES, RAW_DIR, PROCESSED_DIR, GRID_STEP_M

def generate_patches_for_city(city):
    """Generate grid of patch centre points for one city."""
    
    graph_path = RAW_DIR / f"{city['code']}.graphml"
    
    if not graph_path.exists():
        print(f"  {city['code']} graph not found — skipping")
        return []
    
    print(f"  loading {city['name']}...")
    
    # load the saved graph
    G = ox.load_graphml(graph_path)
    
    # get all node coordinates to find city bounding box
    nodes = ox.graph_to_gdfs(G, edges=False)
    lat_min, lat_max = nodes.y.min(), nodes.y.max()
    lon_min, lon_max = nodes.x.min(), nodes.x.max()
    
    # convert grid step from metres to degrees
    # latitude degrees are constant everywhere
    # longitude degrees get narrower as you move away from equator
    step_lat = GRID_STEP_M / 111000
    step_lon = GRID_STEP_M / (111000 * cos(radians(city['lat'])))
    
    # generate grid of centre points
    lat_centres = np.arange(lat_min, lat_max, step_lat)
    lon_centres = np.arange(lon_min, lon_max, step_lon)
    
    patches = []
    patch_count = 0
    
    for lat in lat_centres:
        for lon in lon_centres:
            patches.append({
                'patch_id': f"{city['code']}_{patch_count:05d}",
                'city':     city['name'],
                'code':     city['code'],
                'lat':      round(lat, 6),
                'lon':      round(lon, 6),
            })
            patch_count += 1
    
    print(f"  generated {patch_count} patch centres")
    return patches


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating patch centres for {len(CITIES)} cities...\n")
    
    all_patches = []
    
    for city in CITIES:
        patches = generate_patches_for_city(city)
        all_patches.extend(patches)
    
    # save to CSV
    df = pd.DataFrame(all_patches)
    output_path = PROCESSED_DIR / "patch_centres.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\nTotal patch centres: {len(df)}")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()