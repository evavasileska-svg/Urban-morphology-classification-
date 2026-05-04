import osmnx as ox
from pathlib import Path
import sys

# add repo root to path so we can import config
sys.path.append(str(Path(__file__).parent.parent))
from src.config import CITIES, RAW_DIR

def download_city(city):
    """Download, enrich and save one city graph."""
    
    save_path = RAW_DIR / f"{city['code']}.graphml"
    
    # skip if already downloaded
    if save_path.exists():
        print(f"  {city['code']} already exists — skipping")
        return
    
    print(f"  downloading {city['name']}...")
    
    # download walkable street network
    G = ox.graph_from_place(
        city['name'],
        network_type='walk'
    )
    
    # add compass bearing to every edge
    G = ox.bearing.add_edge_bearings(G)
    
    # save to disk as GraphML
    ox.save_graphml(G, save_path)
    
    print(f"  saved — {G.number_of_nodes()} nodes, "
          f"{G.number_of_edges()} edges")


def main():
    # make sure the raw data folder exists
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {len(CITIES)} cities...\n")
    
    for city in CITIES:
        download_city(city)
    
    print("\nAll cities done.")


if __name__ == "__main__":
    main()