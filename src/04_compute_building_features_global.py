import osmnx as ox
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
from pathlib import Path
from math import cos, radians
from tqdm import tqdm
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.append(str(Path(__file__).parent.parent))
from src.config_global import (
    CITIES,
    PROCESSED_DIR,
    PATCH_SIZE_M,
    GLOBAL_DOWNLOAD_RADIUS_M
)


def get_patch_polygon(centre_lat, centre_lon, patch_size_m):
    """Return patch area as a Shapely polygon in WGS84."""
    delta_lat = (patch_size_m / 2) / 111000
    delta_lon = (patch_size_m / 2) / (
        111000 * cos(radians(centre_lat))
    )
    north = centre_lat + delta_lat
    south = centre_lat - delta_lat
    east  = centre_lon + delta_lon
    west  = centre_lon - delta_lon
    return box(west, south, east, north)


def download_city_buildings(city):
    """Download buildings around the same city-center radius as the graph."""
    print(f"  downloading buildings from point radius...")
    try:
        gdf = ox.features_from_point(
            (city['lat'], city['lon']),
            tags={'building': True},
            dist=GLOBAL_DOWNLOAD_RADIUS_M
        )

        gdf = gdf[gdf.geometry.geom_type.isin(
            ['Polygon', 'MultiPolygon']
        )].copy()

        print(f"  buildings found: {len(gdf)}")
        return gdf

    except Exception as e:
        print(f"  buildings failed: {e}")
        return None


def download_city_open_space(city):
    """
    Download public open space around the same city-center radius.
    Combines parks, grass, and pedestrian areas.
    """
    print(f"  downloading open space from point radius...")
    all_features = []

    tag_queries = [
        {'leisure': 'park'},
        {'landuse': 'grass'},
        {'highway': 'pedestrian'},
    ]

    for tags in tag_queries:
        try:
            gdf = ox.features_from_point(
                (city['lat'], city['lon']),
                tags=tags,
                dist=GLOBAL_DOWNLOAD_RADIUS_M
            )

            if len(gdf) > 0:
                gdf = gdf[gdf.geometry.geom_type.isin(
                    ['Polygon', 'MultiPolygon']
                )].copy()
                all_features.append(gdf)

        except Exception:
            pass

    if not all_features:
        print("  open space found: 0")
        return None

    combined = pd.concat(all_features, ignore_index=True)
    print(f"  open space polygons found: {len(combined)}")
    return combined


def compute_building_features(buildings_gdf, 
                               patch_polygon,
                               patch_area_m2):
    """Compute building type mix and coverage for one patch."""

    empty = {
        'building_count':    0,
        'pct_apartments':    0.0,
        'pct_houses':        0.0,
        'pct_commercial':    0.0,
        'pct_other':         0.0,
        'building_coverage': 0.0,
    }

    if buildings_gdf is None or len(buildings_gdf) == 0:
        return empty

    # clip to patch
    try:
        clip = buildings_gdf[
            buildings_gdf.geometry.intersects(patch_polygon)
        ].copy()
    except Exception:
        return empty

    if len(clip) == 0:
        return empty

    total = len(clip)

    # building type classification
    if 'building' in clip.columns:
        btypes = clip['building'].fillna('yes').str.lower()
    else:
        btypes = pd.Series(['yes'] * total)

    apartment_tags  = ['apartments', 'apartment', 'residential',
                       'block', 'flat']
    house_tags      = ['house', 'detached', 'semidetached_house',
                       'terrace', 'bungalow']
    commercial_tags = ['commercial', 'retail', 'office',
                       'supermarket', 'shop']

    pct_apt  = btypes.isin(apartment_tags).sum() / total
    pct_house = btypes.isin(house_tags).sum() / total
    pct_comm  = btypes.isin(commercial_tags).sum() / total
    pct_other = 1 - pct_apt - pct_house - pct_comm

    # building coverage ratio — project to metres first
    try:
        clip_proj = clip.to_crs('EPSG:3857')
        total_footprint = clip_proj.geometry.area.sum()
        coverage = min(total_footprint / patch_area_m2, 1.0)
    except Exception:
        coverage = 0.0

    return {
        'building_count':    total,
        'pct_apartments':    round(pct_apt, 4),
        'pct_houses':        round(pct_house, 4),
        'pct_commercial':    round(pct_comm, 4),
        'pct_other':         round(pct_other, 4),
        'building_coverage': round(coverage, 4),
    }


def compute_public_space_features(open_space_gdf,
                                   patch_polygon,
                                   patch_area_m2):
    """
    Compute public space ratio for one patch.
    Clips city-wide open space data to patch locally —
    no API calls per patch.
    """
    if open_space_gdf is None or len(open_space_gdf) == 0:
        return {'public_space_ratio': 0.0}

    try:
        # clip open space to patch boundary
        clip = open_space_gdf[
            open_space_gdf.geometry.intersects(patch_polygon)
        ].copy()

        if len(clip) == 0:
            return {'public_space_ratio': 0.0}

        # project to metres for accurate area calculation
        clip_proj = clip.to_crs('EPSG:3857')

        # project patch polygon too
        patch_gdf = gpd.GeoSeries(
            [patch_polygon], crs='EPSG:4326'
        ).to_crs('EPSG:3857')
        patch_proj = patch_gdf.iloc[0]

        # intersect each open space polygon with patch
        # and sum the areas
        total_open = clip_proj.geometry.apply(
            lambda g: g.intersection(patch_proj).area
        ).sum()

        ratio = min(total_open / patch_area_m2, 1.0)

    except Exception:
        ratio = 0.0

    return {'public_space_ratio': round(ratio, 4)}


def get_patch_area_m2(centre_lat, patch_size_m):
    """Compute patch area in m² using projected coordinates."""
    # approximate — good enough for normalisation
    return patch_size_m ** 2


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # load valid patches
    graph_path = PROCESSED_DIR / "graph_features.csv"
    if not graph_path.exists():
        print("graph_features.csv not found.")
        return

    patches = pd.read_csv(graph_path)
    print(f"Loaded {len(patches)} valid patches\n")

    # load existing results if they exist
    output_path = PROCESSED_DIR / "building_features.csv"
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

        # download city-wide data once
        buildings_gdf  = download_city_buildings(city)
        open_space_gdf = download_city_open_space(city)

        patch_area_m2 = get_patch_area_m2(
            city['lat'], PATCH_SIZE_M
        )

        for _, row in tqdm(city_patches.iterrows(),
                           total=len(city_patches),
                           desc=f"  {city['code']}"):

            patch_polygon = get_patch_polygon(
                row['lat'], row['lon'], PATCH_SIZE_M
            )

            building_feats = compute_building_features(
                buildings_gdf, patch_polygon, patch_area_m2
            )
            public_feats = compute_public_space_features(
                open_space_gdf, patch_polygon, patch_area_m2
            )

            result = {
                'patch_id': row['patch_id'],
                'city':     row['city'],
                'code':     row['code'],
                'lat':      row['lat'],
                'lon':      row['lon'],
            }
            result.update(building_feats)
            result.update(public_feats)
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
    print(df[['building_count', 'building_coverage',
              'pct_apartments', 'public_space_ratio']].describe())


if __name__ == "__main__":
    main()