##Section 1 — File paths

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

OPENTOPO_API_KEY = os.getenv("OPENTOPO_API_KEY")

# root of the repo — two levels up from this file
ROOT = Path(__file__).parent.parent

# data folders
RAW_DIR = ROOT / "data" / "raw_global"
URBAN_ATLAS_DIR   = ROOT / "data" / "urban_atlas"
PROCESSED_DIR = ROOT / "data" / "processed_global"
RESULTS_DIR = ROOT / "results" / "global"

##Section 2 — Patch parameters

PATCH_SIZE_M      = 500    # geographic size of each patch in metres
GRID_STEP_M       = 250    # spacing between patch centres (50% overlap)
MIN_SEGMENTS      = 30     # minimum street segments for a valid patch
N_CIRCUITY_PAIRS  = 150    # OD pairs sampled for circuity computation
N_BEARING_BINS    = 36     # bins for entropy histogram
MIN_COVERAGE      = 0.60   # minimum UA class coverage to accept a label
GLOBAL_DOWNLOAD_RADIUS_M = 5000 # radius for downloading OSM data around city centre

##Section 3 — Urban Atlas class mapping

UA_CLASS_MAP = {
    11100: {"label": 0, "name": "continuous_urban"},
    11210: {"label": 1, "name": "dense_urban"},
    11220: {"label": 2, "name": "medium_density"},
    11230: {"label": 3, "name": "low_density"},
}

# UA codes to exclude entirely
UA_EXCLUDE = [11240, 11300, 11400]

##Section 4 — City list

CITIES = [
    {
        "name": "Cairo, Egypt",
        "code": "cairo",
        "lat": 30.0444,
        "lon": 31.2357,
        "continent": "africa",
        "country": "egypt",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Marrakesh, Morocco",
        "code": "marrakesh",
        "lat": 31.6295,
        "lon": -7.9811,
        "continent": "africa",
        "country": "morocco",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Tokyo, Japan",
        "code": "tokyo",
        "lat": 35.6762,
        "lon": 139.6503,
        "continent": "asia",
        "country": "japan",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Bangkok, Thailand",
        "code": "bangkok",
        "lat": 13.7563,
        "lon": 100.5018,
        "continent": "asia",
        "country": "thailand",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "New York City, New York, USA",
        "code": "newyork",
        "lat": 40.7128,
        "lon": -74.0060,
        "continent": "americas",
        "country": "usa",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Mexico City, Mexico",
        "code": "mexicocity",
        "lat": 19.4326,
        "lon": -99.1332,
        "continent": "americas",
        "country": "mexico",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
]