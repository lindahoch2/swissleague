from pathlib import Path
import datetime

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = DATA_DIR / 'competition_results'
INTERMEDIATE_DIR = DATA_DIR / 'intermediate'
OUTPUT_DIR = DATA_DIR / 'swisscup_results'

# File Paths
JSON_PATH = DATA_DIR / "swissleague_data_2026.json"
COMPETITION_PATH = DATA_DIR / "swissleague_competitions_2026.json"
LOGO_PATH = DATA_DIR / "swisscup_hf_farbe.png"

# Titles and Info
OVERALL_TITLE = "Swissleague Hike and Fly Overall Ranking"
WOMEN_TITLE = "Swissleague Hike and Fly Female Ranking"
MEN_TITLE = "Swissleague Hike and Fly Male Ranking"
JUNIOR_TITLE = "Swissleague Hike and Fly Junior Ranking (U26)"
INFO_TEXT = "For feedbacks, please contact: sport@shv-fsvl.ch"

# Year for Junior Ranking
CURRENT_YEAR = datetime.datetime.now().year

# File Prefix
FILE_PREFIX = "swisscup_hf_2026"