from pathlib import Path

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

# File Prefix
FILE_PREFIX = "swisscup_hf_2026"

# Competitions List
EXCEL_FILES = [
    "jhf_2026.xlsx", "airtour_2026.xlsx", "engelberg_2026.xlsx",
    "ghf_2026.xlsx", "eigertour_2026.xlsx", "gruyere_2026.xlsx",
    "lungern_2026.xlsx", "flyback_2026.xlsx", "trailfly_2026.xlsx",
    "Vercofly_2026.xlsx", "beizen_2026.xlsx", "belli_2026.xlsx",
    "millets_2026.xlsx"
]
JSON_KEYS = [
    "jhf", "airtour", "engelberg", "ghf", "eiger", "gruyere", "lungern",
    "flyback", "trailfly", "vercofly", "beizen", "belli", "millet"
]
PHYSICAL = [False, False, False, False, False, False, False, False, False, False, False, False, True, True]