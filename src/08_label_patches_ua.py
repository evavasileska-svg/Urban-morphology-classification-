import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import box
from math import cos, radians
from tqdm import tqdm
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.append(str(Path(__file__).parent.parent))
from src.config import (CITIES, PROCESSED_DIR, UA_CLASS_MAP,
                         UA_EXCLUDE, PATCH_SIZE_M, MIN_COVERAGE)


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


def find_ua_file(city_code):
    """Find the FGB file for a city in the urban atlas folder."""
    ua_dir = Path('data/urban_atlas') / city_code
    if not ua_dir.exists():
        return None
    files = list(ua_dir.glob('*.fgb'))
    if not files:
        return None
    return files[0]


def load_ua_data(city_code):
    """
    Load Urban Atlas data for a city.
    Keeps data in EPSG:3035 for accurate spatial joins.
    """
    fgb_path = find_ua_file(city_code)
    if fgb_path is None:
        return None

    try:
        gdf = gpd.read_file(fgb_path)

        # data is in EPSG:3035 — keep it there
        # we will convert patches to match

        # the numeric code column is code_2018
        if 'code_2018' not in gdf.columns:
            print(f"  WARNING: code_2018 column not found")
            print(f"  Available columns: {list(gdf.columns)}")
            return None

        # convert code to integer
        gdf['ua_code'] = pd.to_numeric(
            gdf['code_2018'], errors='coerce'
        ).astype('Int64')

        # keep only relevant classes
        all_relevant = list(UA_CLASS_MAP.keys()) + UA_EXCLUDE
        gdf = gdf[gdf['ua_code'].isin(all_relevant)].copy()

        print(f"  loaded {len(gdf)} UA polygons "
              f"(urban fabric only)")
        return gdf[['ua_code', 'geometry']]

    except Exception as e:
        print(f"  ERROR loading UA data: {e}")
        return None


def assign_label(ua_gdf, centre_lat, centre_lon, patch_size_m):
    """
    Find the dominant Urban Atlas class for a patch.
    Converts patch to EPSG:3035 to match UA data.
    """
    if ua_gdf is None:
        return None

    try:
        # create patch polygon in WGS84 first
        patch_wgs84 = get_patch_polygon(
            centre_lat, centre_lon, patch_size_m
        )

        # convert patch to EPSG:3035 to match UA data
        patch_gdf = gpd.GeoSeries(
            [patch_wgs84], crs='EPSG:4326'
        ).to_crs('EPSG:3035')
        patch_proj = patch_gdf.iloc[0]
        patch_area = patch_proj.area

        # find UA polygons that intersect the patch
        candidates = ua_gdf[
            ua_gdf.geometry.intersects(patch_proj)
        ].copy()

        if len(candidates) == 0:
            return None

        # compute intersection area per UA polygon
        candidates['intersect_area'] = (
            candidates.geometry.apply(
                lambda g: g.intersection(patch_proj).area
            )
        )

        # sum by UA code
        area_by_code = candidates.groupby('ua_code')[
            'intersect_area'
        ].sum()

        if area_by_code.empty:
            return None

        # find dominant class
        dominant_code = int(area_by_code.idxmax())
        dominant_area = area_by_code.max()
        coverage_ratio = dominant_area / patch_area

        # check coverage threshold
        if coverage_ratio < MIN_COVERAGE:
            return None

        # check if excluded
        if dominant_code in UA_EXCLUDE:
            return None

        # check if in our mapping
        if dominant_code not in UA_CLASS_MAP:
            return None

        label      = UA_CLASS_MAP[dominant_code]['label']
        class_name = UA_CLASS_MAP[dominant_code]['name']

        return {
            'ua_code':          dominant_code,
            'ua_coverage':      round(coverage_ratio, 4),
            'morphology_class': label,
            'class_name':       class_name,
        }

    except Exception as e:
        return None


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # load assembled dataset
    dataset_path = PROCESSED_DIR / "dataset_assembled.csv"
    if not dataset_path.exists():
        print("dataset_assembled.csv not found")
        print("Run 07_assemble_dataset.py first")
        return

    df = pd.read_csv(dataset_path)
    print(f"Loaded {len(df)} patches\n")

    all_labelled = []
    total_labelled   = 0
    total_ambiguous  = 0
    total_no_ua      = 0
    total_excluded   = 0

    for city in CITIES:
        city_patches = df[df['code'] == city['code']]

        if len(city_patches) == 0:
            continue

        # check if UA data exists for this city
        ua_file = find_ua_file(city['code'])
        if ua_file is None:
            print(f"{city['name']} — no UA data, skipping "
                  f"{len(city_patches)} patches")
            total_no_ua += len(city_patches)
            continue

        print(f"Processing {city['name']} "
              f"— {len(city_patches)} patches...")

        # load UA data once per city
        ua_gdf = load_ua_data(city['code'])

        if ua_gdf is None:
            print(f"  failed to load UA data — skipping")
            total_no_ua += len(city_patches)
            continue

        city_labelled  = 0
        city_ambiguous = 0
        city_excluded  = 0

        for _, row in tqdm(city_patches.iterrows(),
                           total=len(city_patches),
                           desc=f"  {city['code']}"):

           

            result = assign_label(ua_gdf, row['lat'], row['lon'], PATCH_SIZE_M)

            if result is None:
                city_ambiguous += 1
                total_ambiguous += 1
                continue

            # combine patch features with label
            row_dict = row.to_dict()
            row_dict.update(result)
            all_labelled.append(row_dict)
            city_labelled += 1
            total_labelled += 1

        print(f"  labelled: {city_labelled} · "
              f"ambiguous/excluded: {city_ambiguous}\n")

    # assemble labelled dataset
    labelled_df = pd.DataFrame(all_labelled)

    print(f"\n{'='*50}")
    print(f"Total patches processed: {len(df)}")
    print(f"Successfully labelled:   {total_labelled}")
    print(f"Ambiguous/excluded:      {total_ambiguous}")
    print(f"No UA coverage:          {total_no_ua}")
    print(f"\nClass distribution:")
    if 'morphology_class' in labelled_df.columns:
        class_counts = labelled_df['morphology_class'].value_counts()
        class_names  = labelled_df.groupby(
            'morphology_class'
        )['class_name'].first()
        for cls in sorted(class_counts.index):
            print(f"  Class {cls} ({class_names[cls]:30}): "
                  f"{class_counts[cls]:6} patches")

    # save labelled dataset
    output_path = PROCESSED_DIR / "dataset_labelled.csv"
    labelled_df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()

