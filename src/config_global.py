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
        "name": "Barcelona, Spain",
        "code": "barcelona",
        "lat": 41.3874,
        "lon": 2.1686,
        "continent": "europe",
        "country": "spain",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Paris, France",
        "code": "paris",
        "lat": 48.8566,
        "lon": 2.3522,
        "continent": "europe",
        "country": "france",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "London, United Kingdom",
        "code": "london",
        "lat": 51.5074,
        "lon": -0.1278,
        "continent": "europe",
        "country": "united_kingdom",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Lisbon, Portugal",
        "code": "lisbon",
        "lat": 38.7223,
        "lon": -9.1393,
        "continent": "europe",
        "country": "portugal",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Sarajevo, Bosnia and Herzegovina",
        "code": "sarajevo",
        "lat": 43.8563,
        "lon": 18.4131,
        "continent": "europe",
        "country": "bosnia_and_herzegovina",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Manhattan, New York, USA",
        "code": "manhattan",
        "lat": 40.7831,
        "lon": -73.9712,
        "continent": "americas",
        "country": "usa",
        "dataset_scope": "global_comparison",
        "has_urban_atlas_label": False,
    },
    {
        "name": "Chicago, Illinois, USA",
        "code": "chicago",
        "lat": 41.8781,
        "lon": -87.6298,
        "continent": "americas",
        "country": "usa",
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
]