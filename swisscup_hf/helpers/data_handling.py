from helpers.models import Athlete, CompetitionResult
import pandas as pd
from collections import defaultdict

def renaming_pandas_columns(df: pd.DataFrame):
    # Catch different column naming for birthdate and rename to a consistent name
    df = df.rename(columns={'Birthdate': 'Birth Date'})
    df = df.rename(columns={'Date of birth': 'Birth Date'})

    if 'Glider' not in df.columns:
        # Dynamically find the columns, allowing for slight variations (like 'Manufacturerb')
        manuf_col = next((col for col in df.columns if 'Manufacturer' in col), None)
        model_col = next((col for col in df.columns if 'Model' in col or 'model' in col), None)

        if manuf_col and model_col:
            # Combine the two columns, handling any potential NaN values safely
            df['Glider'] = df[manuf_col].fillna("").astype(str) + " " + df[model_col].fillna("").astype(str)
            df['Glider'] = df['Glider'].str.strip()
        else:
            # Fallback to an empty string if neither Glider nor the split columns are found
            df['Glider'] = ""

    return df

def replace_zero_with_fake(cid, fake_id_counter: int):
    cid_str = str(cid).strip()
    if cid_str.lower() == "nan" or cid_str in ["0", "", "none"]:
        return f"ZZ{fake_id_counter:03d}"
    return cid_str

def _check_civl_id_name_discrepancy(athlete: Athlete, row, resolver):
    for key in ['name', 'first_name']:
        json_val = getattr(athlete, key)
        excel_val = getattr(row, key)

        if json_val.lower().replace(" ", "") != excel_val.lower().replace(" ", ""):
            resolved_val = resolver.resolve_name_discrepancy(
                athlete.civl_id, f"{athlete.first_name} {athlete.name}", key, json_val, excel_val
            )
            setattr(athlete, key, resolved_val)

def _check_and_update_glider(athlete: Athlete, row, resolver):
    old_glider = athlete.glider
    new_glider = str(row.glider).strip()

    # Define what constitutes an "empty" incoming glider
    empty_glider_values = ["", "nan", "-", "none", "null"]

    # If the new glider is empty, keep the old one without asking
    if new_glider.lower() in empty_glider_values:
        return

    if old_glider.lower().replace(" ", "") != new_glider.lower().replace(" ", ""):
        if old_glider == "" or old_glider.lower() in empty_glider_values:
            athlete.glider = new_glider
        else:
            name = f"{athlete.first_name} {athlete.name}"
            athlete.glider = resolver.resolve_glider(name, old_glider, new_glider)

def add_points_to_data(df: pd.DataFrame, num_participants):
    # Formula: 100 - 100 * (rank - 1) / (num_participants -1)
    df['points'] = (100 - (100 * (df['rank'] - 1)) / (num_participants - 1)).clip(lower=1).round(2)

    return num_participants, df

def _resolve_fake_civl_id(json_data, row):
    """Returns the real CIVL ID if a matching fake one is found, else the original."""
    if "Z" in str(row.civl_id):
        for json_civl_id, athlete in json_data.items():
            if athlete.name == row.name and athlete.first_name == row.first_name:
                return json_civl_id
    return row.civl_id

def _process_single_athlete_record(athletes_dict: dict, row, competition_key: str, resolver):
    # row is now a namedtuple from itertuples(), access via dot notation
    civl_id = _resolve_fake_civl_id(athletes_dict, row)

    if civl_id in athletes_dict:
        athlete = athletes_dict[civl_id]
        _check_civl_id_name_discrepancy(athlete, row, resolver)
        _check_and_update_glider(athlete, row, resolver)
        if athlete.birth_year == 0 and row.birth_year != 0:
            athlete.birth_year = row.birth_year
    else:
        # Create new Athlete object
        athlete = Athlete(
            civl_id=civl_id,
            name=row.name,
            first_name=row.first_name,
            gender=row.gender,
            nat=row.nat,
            glider=row.glider,
            birth_year=row.birth_year
        )
        athletes_dict[civl_id] = athlete

    # Add competition and update points
    if competition_key not in athlete.competitions:
        athlete.competitions[competition_key] = CompetitionResult(rank=row.rank, points=row.points)
        athlete.update_total_points(row.points, competition_key)

def add_data_to_json(athletes_dict: dict, df: pd.DataFrame, competition_key: str, resolver):
    # Using itertuples for massive performance gain over iterrows
    for row in df.itertuples(index=False):
        _process_single_athlete_record(athletes_dict, row, competition_key, resolver)


def get_highest_fake_civil_id_already_in_use(json_data):
    # Extract all Fake ID's in use
    existing_fake_ids = [cid for cid in json_data.keys() if cid.startswith("ZZ")]

    if existing_fake_ids:
        max_num = max(int(cid[2:]) for cid in existing_fake_ids)  # take numeric part after "ZZ"
    else:
        max_num = 0  # start fresh if no fake IDs exist

    # New Fake ID must be one number higher
    fake_id_counter = max_num + 1

    return fake_id_counter


def _find_duplicate_athletes(json_data):
    name_map = defaultdict(set)

    # 1. Build the map using a sorted key to handle swapped names automatically
    for civl_id, data in json_data.items():
        name = data.get('name', '').strip().lower()
        first_name = data.get('first_name', '').strip().lower()

        sorted_key = tuple(sorted([name, first_name]))
        name_map[sorted_key].add(civl_id)

    return name_map

def extract_year(date_val):
    if pd.isna(date_val):
        return 0

    # If Pandas already successfully parsed it as a datetime object
    if hasattr(date_val, 'year'):
        return date_val.year

    date_str = str(date_val).strip()

    try:
        # Check if it's in YYYY-MM-DD format
        if '-' in date_str:
            # Splits "1996-09-21 00:00:00" into ["1996", "09", "21 00:00:00"]
            return int(date_str.split('-')[0])

        # Check if it's in DD/MM/YYYY format
        elif '/' in date_str:
            # Splits "21/09/1996" into ["21", "09", "1996"]
            return int(date_str.split('/')[-1])

        # Check if it's just a year (handles "1996", 1996, or "1996.0")
        else:
            year = int(float(date_str))
            return year if 1900 <= year <= 2100 else 0  # Basic sanity check for year range

    except ValueError:
        print(f"⚠️ Unrecognized date format: '{date_str}'. Unable to extract year.")

    return 0

def data_cleaning(athletes_dict: dict, resolver):
    """Iterates through athletes and cleans up inconsistencies."""
    for civl_id, athlete in athletes_dict.items():
        athlete_info = f"{civl_id}: {athlete.name} {athlete.first_name}"
        athlete.glider = _normalize_glider_name(athlete.glider)
        athlete.gender = normalize_gender(athlete.gender, resolver)
        athlete.nat = normalize_nationality(athlete.nat, athlete_info, resolver)

    check_duplicate_athletes(athletes_dict, resolver)


def _normalize_glider_name(glider):
    if pd.isna(glider):
        return ""

    glider = str(glider).lower().strip()

    # Common replacements
    replacements = {
        "six": "6",
        "swift6": "swift 6",
        "7p": "7 p",
        "6p": "6 p",
        "3p": "3 p",
        "volt4": "volt 4",
        "volt5": "volt 5",
        "enzo3": "enzo 3",
        "oxp2": "oxa 2",
        "omegauls": "omega uls",
        "air design": "airdesign",
        "zéolite": "zeolite",
        "apls": "alps",
        "sigma11": "sigma 11",
        "artic": "artik",
    }
    for old, new in replacements.items():
        glider = glider.replace(old, new)

    # Special P-suffix handling
    def fix_p_suffix(model):
        if f"{model} " in glider or f"{model}" in glider:
            if "p" not in glider:
                return glider.replace(model, f"{model} p")
        return glider

    glider = fix_p_suffix("artik 7")
    glider = fix_p_suffix("klimber 3")
    glider = fix_p_suffix("klimber 2")
    glider = fix_p_suffix("ikuma 3")

    # Add manufacturer if missing
    manufacturers = {
        "ozone": ["zeolite", "swift", "lygth", "alpina"],
        "advance": ["omega", "sigma", "iota", "theta"],
        "niviuk": ["artik", "klimber", "hiko", "ikuma"],
        "phi": ["allegro", "scala", "beat"],
        "gin": ["explorer"],
        "airdesign": ["hero", "soar", "volt"],
        "skywalk": ["arak", "sage"],
        "nova": ["mentor", "xenon", "vortex", "codex"],
    }
    for brand, keywords in manufacturers.items():
        if any(k in glider for k in keywords) and brand not in glider:
            glider = f"{brand} {glider}"
            break

    # Title-case + brand-specific fixes
    glider = glider.title()
    brand_fixes = {
        "Airdesign": "AirDesign", "Phi": "PHI", "Supair": "SupAir",
        "Uls": "ULS", "Dls": "DLS", "Rs": "RS", "Gt": "GT", "Bgd": "BGD",
    }
    for wrong, correct in brand_fixes.items():
        glider = glider.replace(wrong, correct)

    return glider


def normalize_gender(gender, resolver):
    gender = str(gender).strip().upper()
    if gender == "W":
        gender = "F"

    while len(gender) > 1 or gender not in ["M", "F"]:
        gender = resolver.resolve_invalid_gender(gender)

    return gender


def normalize_nationality(nationality, info, resolver):
    if pd.isna(nationality) or not isinstance(nationality, str):
        nationality = ""
    else:
        nationality = nationality.strip().upper()

    replacements = {
        "CH": "SUI", "IT": "ITA", "UK": "GBR", "FR": "FRA",
        "F": "FRA", "NZ": "NZL", "D": "DEU", "AT": "AUT",
        "DK": "DNK", "UY": "URY", "DE": "DEU",
    }

    if nationality in replacements:
        nationality = replacements[nationality]

    while len(nationality) != 3:
        nationality = resolver.resolve_invalid_nationality(nationality, info)
        if nationality in replacements:
            nationality = replacements[nationality]

    return nationality


def _find_duplicate_athletes(athletes_dict):
    name_map = defaultdict(set)
    # Build the map using a sorted key to handle swapped names automatically
    for civl_id, athlete in athletes_dict.items():
        name = athlete.name.strip().lower()
        first_name = athlete.first_name.strip().lower()
        sorted_key = tuple(sorted([name, first_name]))
        name_map[sorted_key].add(civl_id)

    return name_map


def check_duplicate_athletes(athletes_dict, resolver):
    name_map = _find_duplicate_athletes(athletes_dict)

    for key, ids in name_map.items():
        unique_ids = [cid for cid in ids if cid in athletes_dict]

        if len(unique_ids) > 1:
            name_title = f"{key[0].title()} {key[1].title()}"
            is_merge, target_id = resolver.resolve_duplicate_merge(name_title, unique_ids)

            if is_merge and target_id in unique_ids:
                _merge_duplicate_athletes(unique_ids, target_id, athletes_dict)
            elif is_merge:
                print("Invalid target ID entered. Skipping merge...")
            else:
                print("Cancelled merge. Skipping...")


def _merge_duplicate_athletes(unique_ids, target_id, athletes_dict):
    source_ids = [cid for cid in unique_ids if cid != target_id]
    target_athlete = athletes_dict[target_id]

    for source_id in source_ids:
        if source_id not in athletes_dict:
            continue

        source_athlete = athletes_dict[source_id]

        # Transfer competitions
        for comp_key, comp_data in source_athlete.competitions.items():
            if comp_key in target_athlete.competitions:
                # Keep the higher score
                if comp_data.points > target_athlete.competitions[comp_key].points:
                    target_athlete.competitions[comp_key] = comp_data
            else:
                target_athlete.competitions[comp_key] = comp_data

        # Delete the duplicate record
        del athletes_dict[source_id]

    # Recalculate total points for the survivor by resetting counts
    for k in target_athlete.competitions:
        target_athlete.competitions[k].counts = False

    # Get the top 4 comps
    top_comps = sorted(target_athlete.competitions.items(), key=lambda x: x[1].points, reverse=True)[:4]

    total_points = 0
    for comp_key, comp_data in top_comps:
        target_athlete.competitions[comp_key].counts = True
        total_points += comp_data.points

    target_athlete.total_points = round(total_points, 2)
    print(f"✅ Successfully merged into {target_id}.")

def clean_dataframe_text(df):
    df['civl_id'] = df['civl_id'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df['name'] = df['name'].str.strip().str.title()
    df['first_name'] = df['first_name'].str.strip().str.title()

    # Apply normalization to incoming Excel data immediately
    df['glider'] = df['glider'].apply(_normalize_glider_name)

    return df