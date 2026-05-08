import osmnx as ox
import numpy as np
import pandas as pd
import requests
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import from_bounds
from pathlib import Path
from math import cos, radians, log
from tqdm import tqdm
from shapely.geometry import box
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.append(str(Path(__file__).parent.parent))
from src.config_global import (
    CITIES,
    PROCESSED_DIR,
    RAW_DIR,
    PATCH_SIZE_M,
    OPENTOPO_API_KEY,
    GLOBAL_DOWNLOAD_RADIUS_M
)


# ── POI CATEGORY MAPPING ─────────────────────────────────────────

AMENITY_CATEGORIES = {
    'food_drink':  ['restaurant', 'cafe', 'bar', 'pub',
                    'fast_food', 'food_court', 'biergarten'],
    'retail':      ['marketplace', 'pharmacy'],
    'civic':       ['school', 'university', 'college', 'hospital',
                    'clinic', 'doctors', 'library', 'post_office',
                    'police', 'fire_station', 'townhall',
                    'courthouse', 'embassy', 'community_centre'],
    'transport':   ['bus_station', 'taxi', 'bicycle_parking',
                    'parking', 'fuel', 'car_wash'],
    'culture':     ['theatre', 'cinema', 'museum', 'arts_centre',
                    'nightclub', 'casino', 'place_of_worship'],
    'services':    ['bank', 'atm', 'bureau_de_change', 'dentist',
                    'veterinary', 'laundry', 'dry_cleaning',
                    'internet_cafe'],
}

SHOP_CATEGORIES = {
    'retail': ['supermarket', 'convenience', 'bakery', 'butcher',
               'clothes', 'shoes', 'electronics', 'furniture',
               'hardware', 'florist', 'books', 'sports',
               'department_store', 'mall', 'kiosk'],
}


# ── GEOMETRY HELPERS ─────────────────────────────────────────────

def get_patch_polygon(centre_lat, centre_lon, patch_size_m):
    """Return patch bounding box as Shapely polygon in WGS84."""
    delta_lat = (patch_size_m / 2) / 111000
    delta_lon = (patch_size_m / 2) / (
        111000 * cos(radians(centre_lat))
    )
    return box(
        centre_lon - delta_lon,
        centre_lat - delta_lat,
        centre_lon + delta_lon,
        centre_lat + delta_lat,
    )


def get_city_bbox(G):
    """Get bounding box of a city graph with a small margin."""
    nodes = ox.graph_to_gdfs(G, edges=False)
    margin = 0.02  # ~2km buffer around city edges
    return (
        nodes.y.max() + margin,  # north
        nodes.y.min() - margin,  # south
        nodes.x.max() + margin,  # east
        nodes.x.min() - margin,  # west
    )


# ── TERRAIN ──────────────────────────────────────────────────────

def download_city_srtm(city_code, north, south, east, west,
                        api_key):
    """
    Download SRTM elevation raster for entire city bounding box.
    Saves to data/raw/ as a GeoTIFF.
    Returns path to saved file.
    """
    save_path = RAW_DIR / f"{city_code}_srtm.tif"

    # skip if already downloaded
    if save_path.exists():
        print(f"  SRTM already exists for {city_code} — skipping")
        return save_path

    print(f"  downloading SRTM for {city_code}...")

    url = "https://portal.opentopography.org/API/globaldem"
    params = {
        'demtype':      'SRTMGL1',
        'south':        south,
        'north':        north,
        'west':         west,
        'east':         east,
        'outputFormat': 'GTiff',
        'API_Key':      api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=120)
        if response.status_code == 200:
            save_path.write_bytes(response.content)
            print(f"  SRTM saved — {save_path.stat().st_size // 1024} KB")
            return save_path
        else:
            print(f"  SRTM download failed: {response.status_code}")
            print(f"  response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  SRTM error: {e}")
        return None


def compute_slope_from_array(elevation):
    """Compute slope in degrees from elevation array."""
    cell_size_m = 30.0
    elev = np.where(np.isnan(elevation), 0, elevation)
    dy, dx = np.gradient(elev, cell_size_m)
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    slope[np.isnan(elevation)] = np.nan
    return slope


def sample_terrain_for_patch(srtm_path, centre_lat, centre_lon,
                              patch_size_m):
    """
    Sample SRTM raster for one patch from local file.
    No API call — reads from disk.
    """
    empty = {
        'mean_slope_deg':     np.nan,
        'max_slope_deg':      np.nan,
        'elevation_variance': np.nan,
    }

    if srtm_path is None or not srtm_path.exists():
        return empty

    delta_lat = (patch_size_m / 2) / 111000
    delta_lon = (patch_size_m / 2) / (
        111000 * cos(radians(centre_lat))
    )

    west  = centre_lon - delta_lon
    east  = centre_lon + delta_lon
    south = centre_lat - delta_lat
    north = centre_lat + delta_lat

    try:
        with rasterio.open(srtm_path) as src:
            # read only the window corresponding to this patch
            window = from_bounds(
                west, south, east, north,
                src.transform
            )
            elevation = src.read(1, window=window).astype(float)

            # handle no-data
            if src.nodata is not None:
                elevation[elevation == src.nodata] = np.nan

            if elevation.size == 0:
                return empty

            slope = compute_slope_from_array(elevation)

            slope_flat = slope[~np.isnan(slope)].flatten()
            elev_flat  = elevation[~np.isnan(elevation)].flatten()

            if len(slope_flat) == 0:
                return empty

            return {
                'mean_slope_deg':
                    round(float(np.mean(slope_flat)), 4),
                'max_slope_deg':
                    round(float(np.max(slope_flat)), 4),
                'elevation_variance':
                    round(float(np.var(elev_flat)), 4),
            }

    except Exception as e:
        return empty


# ── FUNCTIONAL DIVERSITY ─────────────────────────────────────────

def download_city_pois(city):
    """Download POIs around the same city-center radius as the graph."""
    print(f"  downloading POIs from point radius...")
    all_pois = []

    for tags, source in [({'amenity': True}, 'amenity'),
                         ({'shop': True}, 'shop')]:
        try:
            gdf = ox.features_from_point(
                (city['lat'], city['lon']),
                tags=tags,
                dist=GLOBAL_DOWNLOAD_RADIUS_M
            )

            if len(gdf) > 0:
                gdf = gdf[
                    gdf.geometry.geom_type == 'Point'
                ].copy()

                gdf['category_source'] = source
                tag_col = list(tags.keys())[0]

                if tag_col in gdf.columns:
                    gdf['poi_type'] = gdf[tag_col]

                all_pois.append(gdf)

        except Exception as e:
            print(f"  {source} download failed: {e}")

    if not all_pois:
        print("  POIs found: 0")
        return None

    combined = pd.concat(all_pois, ignore_index=True)
    print(f"  POIs found: {len(combined)}")
    return combined


def classify_poi(poi_type, source):
    """Map OSM POI type to simplified functional category."""
    poi_type = str(poi_type).lower()
    lookup = AMENITY_CATEGORIES if source == 'amenity' \
             else SHOP_CATEGORIES
    for category, tags in lookup.items():
        if poi_type in tags:
            return category
    return 'retail' if source == 'shop' else 'other'


def shannon_entropy(counts_dict):
    """Shannon entropy normalised to 0-1."""
    total = sum(counts_dict.values())
    if total == 0:
        return 0.0
    proportions = [v / total for v in counts_dict.values() if v > 0]
    H = -sum(p * log(p) for p in proportions)
    n = sum(1 for v in counts_dict.values() if v > 0)
    return H / log(n) if n > 1 else 0.0


def compute_poi_features(pois_gdf, patch_polygon, patch_size_m):
    """Compute functional diversity features for one patch."""
    patch_area_km2 = (patch_size_m / 1000) ** 2

    empty = {
        'poi_count':          0,
        'poi_density':        0.0,
        'functional_entropy': 0.0,
        'n_poi_categories':   0,
        'pct_food_drink':     0.0,
        'pct_retail':         0.0,
        'pct_civic':          0.0,
        'pct_culture':        0.0,
        'pct_transport':      0.0,
        'pct_services':       0.0,
    }

    if pois_gdf is None or len(pois_gdf) == 0:
        return empty

    try:
        clip = pois_gdf[
            pois_gdf.geometry.within(patch_polygon)
        ].copy()
    except Exception:
        return empty

    if len(clip) == 0:
        return empty

    total = len(clip)

    # classify POIs
    if 'poi_type' in clip.columns and \
       'category_source' in clip.columns:
        clip['func_cat'] = clip.apply(
            lambda r: classify_poi(
                r.get('poi_type', 'other'),
                r.get('category_source', 'amenity')
            ), axis=1
        )
    else:
        clip['func_cat'] = 'other'

    # count by category
    all_cats = ['food_drink', 'retail', 'civic',
                'culture', 'transport', 'services', 'other']
    counts = clip['func_cat'].value_counts().to_dict()
    for cat in all_cats:
        counts.setdefault(cat, 0)

    func_entropy = shannon_entropy(counts)
    n_cats = sum(1 for v in counts.values() if v > 0)

    return {
        'poi_count':
            total,
        'poi_density':
            round(total / patch_area_km2, 2),
        'functional_entropy':
            round(func_entropy, 4),
        'n_poi_categories':
            n_cats,
        'pct_food_drink':
            round(counts.get('food_drink', 0) / total, 4),
        'pct_retail':
            round(counts.get('retail', 0) / total, 4),
        'pct_civic':
            round(counts.get('civic', 0) / total, 4),
        'pct_culture':
            round(counts.get('culture', 0) / total, 4),
        'pct_transport':
            round(counts.get('transport', 0) / total, 4),
        'pct_services':
            round(counts.get('services', 0) / total, 4),
    }


# ── MAIN ─────────────────────────────────────────────────────────

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    graph_path = PROCESSED_DIR / "graph_features.csv"
    if not graph_path.exists():
        print("graph_features.csv not found.")
        return

    patches = pd.read_csv(graph_path)
    print(f"Loaded {len(patches)} valid patches\n")

    # load existing results if they exist
    output_path = PROCESSED_DIR / "terrain_poi_features.csv"
    if output_path.exists():
        existing = pd.read_csv(output_path)
        existing_ids = set(existing['patch_id'].values)
        print(f"Found {len(existing)} existing — skipping")
        all_rows = existing.to_dict('records')
    else:
        existing_ids = set()
        all_rows = []

    for city in CITIES:
        city_patches = patches[patches['code'] == city['code']]

        # skip already computed patches
        city_patches = city_patches[
            ~city_patches['patch_id'].isin(existing_ids)
        ]

        if len(city_patches) == 0:
            print(f"{city['name']} — already done, skipping")
            continue

        print(f"\nProcessing {city['name']} "
              f"— {len(city_patches)} patches...")

        # load cached city graph to get bounding box
        graph_file = RAW_DIR / f"{city['code']}.graphml"
        if not graph_file.exists():
            print(f"  graph not found — skipping")
            continue

        G = ox.load_graphml(graph_file)
        north, south, east, west = get_city_bbox(G)

        # download SRTM once per city
        srtm_path = download_city_srtm(
            city['code'], north, south, east, west,
            OPENTOPO_API_KEY
        )

        # download POIs once per city
        pois_gdf = download_city_pois(city)

        for _, row in tqdm(city_patches.iterrows(),
                           total=len(city_patches),
                           desc=f"  {city['code']}"):

            patch_polygon = get_patch_polygon(
                row['lat'], row['lon'], PATCH_SIZE_M
            )

            terrain_feats = sample_terrain_for_patch(
                srtm_path, row['lat'], row['lon'], PATCH_SIZE_M
            )

            poi_feats = compute_poi_features(
                pois_gdf, patch_polygon, PATCH_SIZE_M
            )

            result = {
                'patch_id': row['patch_id'],
                'city':     row['city'],
                'code':     row['code'],
                'lat':      row['lat'],
                'lon':      row['lon'],
            }
            result.update(terrain_feats)
            result.update(poi_feats)
            all_rows.append(result)

        # save after each city
        df = pd.DataFrame(all_rows)
        df.to_csv(output_path, index=False)
        print(f"  saved — {len(df)} total patches so far")

    # final save
    df = pd.DataFrame(all_rows)
    df.to_csv(output_path, index=False)

    print(f"\nTotal patches: {len(df)}")
    print(f"Saved to {output_path}")
    print(df[['mean_slope_deg', 'poi_count',
              'functional_entropy']].describe())


if __name__ == "__main__":
    main()