##Section 1 — File paths

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

OPENTOPO_API_KEY = os.getenv("OPENTOPO_API_KEY")

# root of the repo — two levels up from this file
ROOT = Path(__file__).parent.parent

# data folders
RAW_DIR           = ROOT / "data" / "raw"
URBAN_ATLAS_DIR   = ROOT / "data" / "urban_atlas"
PROCESSED_DIR     = ROOT / "data" / "processed"
RESULTS_DIR       = ROOT / "results"

##Section 2 — Patch parameters

PATCH_SIZE_M      = 500    # geographic size of each patch in metres
GRID_STEP_M       = 250    # spacing between patch centres (50% overlap)
MIN_SEGMENTS      = 30     # minimum street segments for a valid patch
N_CIRCUITY_PAIRS  = 150    # OD pairs sampled for circuity computation
N_BEARING_BINS    = 36     # bins for entropy histogram
MIN_COVERAGE      = 0.60   # minimum UA class coverage to accept a label

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
    # ── original 8 ───────────────────────────────────────────────

    {
        "name":   "Vienna, Austria",
        "code":   "vienna",
        "lat":    48.2082,
        "lon":    16.3738,
    },
    {
        "name":   "Prague, Czech Republic",
        "code":   "prague",
        "lat":    50.0755,
        "lon":    14.4378,
    },
    {
        "name":   "Barcelona, Spain",
        "code":   "barcelona",
        "lat":    41.3851,
        "lon":     2.1734,
    },
    {
        "name":   "Amsterdam, Netherlands",
        "code":   "amsterdam",
        "lat":    52.3676,
        "lon":     4.9041,
    },
    {
        "name":   "Sarajevo, Bosnia and Herzegovina",
        "code":   "sarajevo",
        "lat":    43.8563,
        "lon":    18.4131,
    },
    {
        "name":   "Warsaw, Poland",
        "code":   "warsaw",
        "lat":    52.2297,
        "lon":    21.0122,
    },
    {
        "name":   "Skopje, North Macedonia",
        "code":   "skopje",
        "lat":    41.9973,
        "lon":    21.4280,
    },
    {
        "name":   "Riga, Latvia",
        "code":   "riga",
        "lat":    56.9460,
        "lon":    24.1059,
    },

    # ── new cities — class 0 historic dense ──────────────────────

    {
        "name":   "Tallinn, Estonia",
        "code":   "tallinn",
        "lat":    59.4370,
        "lon":    24.7536,
    },
    {
        "name":   "Bologna, Italy",
        "code":   "bologna",
        "lat":    44.4949,
        "lon":    11.3426,
    },
    {
        "name":   "Ghent, Belgium",
        "code":   "ghent",
        "lat":    51.0543,
        "lon":     3.7174,
    },

    # ── new cities — class 1 planned grid ────────────────────────

    {
        "name":   "Budapest, Hungary",
        "code":   "budapest",
        "lat":    47.4979,
        "lon":    19.0402,
    },
    {
        "name":   "Turin, Italy",
        "code":   "turin",
        "lat":    45.0703,
        "lon":     7.6869,
    },
    {
        "name":   "Thessaloniki, Greece",
        "code":   "thessaloniki",
        "lat":    40.6401,
        "lon":    22.9444,
    },
    {
        "name":   "Brussels, Belgium",
        "code":   "brussels",
        "lat":    50.8503,
        "lon":     4.3517,
    },
    {
        "name":   "Lisbon, Portugal",
        "code":   "lisbon",
        "lat":    38.7169,
        "lon":    -9.1395,
    },

    # ── new cities — class 2 socialist modernist ─────────────────

    {
        "name":   "Bucharest, Romania",
        "code":   "bucharest",
        "lat":    44.4268,
        "lon":    26.1025,
    },
    {
        "name":   "Sofia, Bulgaria",
        "code":   "sofia",
        "lat":    42.6977,
        "lon":    23.3219,
    },
    {
        "name":   "Vilnius, Lithuania",
        "code":   "vilnius",
        "lat":    54.6872,
        "lon":    25.2797,
    },
    {
        "name":   "Bratislava, Slovakia",
        "code":   "bratislava",
        "lat":    48.1486,
        "lon":    17.1077,
    },

    # ── new cities — class 3 suburban low density ─────────────────

    {
        "name":   "Dublin, Ireland",
        "code":   "dublin",
        "lat":    53.3498,
        "lon":    -6.2603,
    },
    {
        "name":   "Helsinki, Finland",
        "code":   "helsinki",
        "lat":    60.1699,
        "lon":    24.9384,
    },
    {
        "name":   "Stockholm, Sweden",
        "code":   "stockholm",
        "lat":    59.3293,
        "lon":    18.0686,
    },
    {
        "name":   "Rotterdam, Netherlands",
        "code":   "rotterdam",
        "lat":    51.9244,
        "lon":     4.4777,
    },

    # ── new cities — geographic diversity ────────────────────────

    {
        "name":   "Tel Aviv-Yafo, Israel",
        "code":   "telaviv",
        "lat":    32.0853,
        "lon":    34.7818,
    },
    {
    "name":   "Marrakesh, Morocco",
    "code":   "marrakesh",
    "lat":    31.6295,
    "lon":    -7.9811,
},
]