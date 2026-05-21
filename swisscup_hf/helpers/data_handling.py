import pandas as pd
from collections import defaultdict


def _check_civl_id_name_discrepancy(json_data, row):
    civl_id = str(row['civl_id'])

    for key in ['name', 'first_name']:
        json_val = str(json_data[civl_id][key])
        excel_val = str(row[key])

        # Create normalized versions for comparison: lowercase and no spaces
        json_comp = json_val.lower().replace(" ", "")
        excel_comp = excel_val.lower().replace(" ", "")

        # Only prompt if the normalized strings actually differ
        if json_comp != excel_comp:
            print(f"\n⚠️ Discrepancy found for civl_id {civl_id} ({json_data[civl_id]['first_name']} {json_data[civl_id]['name']}) in {key.replace('_', ' ').title()}:")
            print(f"  [1] JSON value:  {json_val}")
            print(f"  [2] Excel value: {excel_val}")

            while True:
                choice = input(f"Which value should be kept? (1/2): ").strip()
                if choice == '1':
                    # Do nothing, keep existing JSON data
                    break
                elif choice == '2':
                    # Update JSON with Excel data
                    json_data[civl_id][key] = excel_val
                    break
                else:
                    print("Invalid input. Please enter 1 or 2.")


def _glider_user_interaction(name, old_glider, new_glider):
    print(f"\n🪂 Discrepancy in glider found for {name}:")
    print(f"  [1] Old glider (JSON):  {old_glider}")
    print(f"  [2] New glider (Excel): {new_glider}")
    print(f"  [3] Type a custom glider name")

    while True:
        choice = input("Which glider should be used? (1/2/3): ").strip()
        if choice == '1': return old_glider
        if choice == '2': return new_glider
        if choice == '3': return input("Enter custom glider name: ").strip()
        print("Invalid input.")


def _check_and_update_glider(json_data, row):
    civl_id = str(row['civl_id'])
    old_glider = str(json_data[civl_id]['glider'])
    new_glider = str(row['glider'])

    # Create normalized versions for comparison: lowercase and no spaces
    old_comp = old_glider.lower().replace(" ", "")
    new_comp = new_glider.lower().replace(" ", "")

    if old_comp != new_comp:
        if old_comp == "":
            json_data[civl_id]['glider'] = new_glider
        else:
            name = f"{json_data[civl_id]['first_name']} {json_data[civl_id]['name']}"
            # Call the UI function, then update the data
            resolved_glider = _glider_user_interaction(name, old_glider, new_glider)
            json_data[civl_id]['glider'] = resolved_glider


def add_points_to_data(df: pd.DataFrame, num_participants):
    # Formula: 100 - 100 * (rank - 1) / (num_participants -1)
    df['points'] = (100 - (100 * (df['rank'] - 1)) / (num_participants - 1)).clip(lower=1).round(2)

    return num_participants, df


def _check_if_competition_already_exists(json_data, civil_id, competition_key):
    if competition_key in json_data[civil_id]["competitions"]:
      print(f"Competition {competition_key} already exists for civl_id {civil_id}")
      return True
    return False


def _add_competition_data(json_data, data_row, competition_key):
    json_data[str(data_row['civl_id'])]["competitions"][competition_key] = {
        "rank": data_row['rank'],
        "points": data_row['points'],
        "counts": True
    }
    return json_data


def _update_total_points(json_data, civil_id:str, new_points, new_comp_key):
    athletes_comp_keys = json_data[civil_id]["competitions"].keys()
    if len(athletes_comp_keys) <= 4:
        total_points = json_data[civil_id]["total_points"] + new_points
        json_data[civil_id]["total_points"] = round(total_points, 2)

    else:
        # Find lowest points from previous comps
        lowest_points = new_points
        lowest_key = new_comp_key

        for comp_key in athletes_comp_keys:
            if json_data[civil_id]["competitions"][comp_key]['counts'] and json_data[civil_id]["competitions"][comp_key]['points'] < lowest_points:
              lowest_points = json_data[civil_id]["competitions"][comp_key]['points']
              lowest_key = comp_key

        # update remove lowest_competition from total points
        json_data[civil_id]["competitions"][lowest_key]['counts'] = False
        json_data[civil_id]["total_points"] += new_points - lowest_points
        json_data[civil_id]["total_points"] = round(json_data[civil_id]["total_points"], 2)
    return json_data


def _add_athlete_data(json_data, data_row):
    print()
    print(f"Adding athlete data for civl_id {data_row['civl_id']}")
    json_data[str(data_row['civl_id'])] = {
        "name": data_row['name'],
        "first_name": data_row['first_name'],
        "gender": data_row['gender'],
        "birth_year": data_row['birth_year'],
        "total_points": 0,
        "nat": data_row['nat'],
        "glider": data_row['glider'],
        "competitions": {}
    }
    return json_data


def _resolve_fake_civl_id(json_data, row):
    """Returns the real CIVL ID if a matching fake one is found, else the original."""
    if "Z" in str(row['civl_id']):
        for json_civl_id, athlete in json_data.items():
            if athlete['name'] == row['name'] and athlete['first_name'] == row['first_name']:
                return json_civl_id
    return row['civl_id']


def _process_single_athlete_record(json_data, row, competition_key):
    """Handles the full flow for a single athlete row."""
    row['civl_id'] = _resolve_fake_civl_id(json_data, row)
    civl_id = str(row['civl_id'])

    if civl_id in json_data:
        _check_civl_id_name_discrepancy(json_data, row)
        _check_and_update_glider(json_data, row)

        # Add birth year if it was previously missing in the JSON
        if json_data[civl_id].get('birth_year', 0) == 0 and row['birth_year'] != 0:
            json_data[civl_id]['birth_year'] = row['birth_year']
    else:
        _add_athlete_data(json_data, row)

    if not _check_if_competition_already_exists(json_data, civl_id, competition_key):
        _add_competition_data(json_data, row, competition_key)
        _update_total_points(json_data, civl_id, row['points'], competition_key)


def add_data_to_json(json_data: dict, df: pd.DataFrame, competition_key: str):
    """Main entry point. Now incredibly clean and readable."""
    for _, row in df.iterrows():
        _process_single_athlete_record(json_data, row, competition_key)

    return json_data


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


def normalize_glider_name(glider):
    if pd.isna(glider):
        return ""

    glider = glider.lower().strip()

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
        "Airdesign": "AirDesign",
        "Phi": "PHI",
        "Supair": "SupAir",
        "Uls": "ULS",
        "Dls": "DLS",
        "Rs": "RS",
        "Gt": "GT",
    }
    for wrong, correct in brand_fixes.items():
        glider = glider.replace(wrong, correct)

    return glider


def _find_duplicate_athletes(json_data):
    name_map = defaultdict(set)

    # 1. Build the map using a sorted key to handle swapped names automatically
    for civl_id, data in json_data.items():
        name = data.get('name', '').strip().lower()
        first_name = data.get('first_name', '').strip().lower()

        sorted_key = tuple(sorted([name, first_name]))
        name_map[sorted_key].add(civl_id)

    return name_map


def _duplicate_athletes_user_interaction(key, unique_ids):
    print(f"\n👯 Possible duplicate: {key[0].title()} {key[1].title()}")
    print(f"CIVL IDs found: {', '.join(unique_ids)}")

    action = input("Do you want to merge these records? (y/n): ").strip().lower()
    if action == 'y':
        print("Available IDs:", unique_ids)
        target_id = input("Type the exact CIVL ID to KEEP (or press Enter to cancel): ").strip()
        return True, target_id

    else:
        return False, None


def _merge_duplicate_athletes(unique_ids, target_id, json_data):
    source_ids = [cid for cid in unique_ids if cid != target_id]

    for source_id in source_ids:
        # Safety check: ensure source_id wasn't already deleted
        if source_id not in json_data:
            continue

        # Transfer competitions
        for comp_key, comp_data in json_data[source_id]["competitions"].items():
            if comp_key in json_data[target_id]["competitions"]:
                if comp_data["points"] > json_data[target_id]["competitions"][comp_key]["points"]:
                    json_data[target_id]["competitions"][comp_key] = comp_data
            else:
                json_data[target_id]["competitions"][comp_key] = comp_data

        # Delete the duplicate
        del json_data[source_id]

    # Recalculate total points for the survivor
    target_comps = json_data[target_id]["competitions"]
    for k in target_comps:
        target_comps[k]["counts"] = False

    top_comps = sorted(target_comps.items(), key=lambda x: x[1]["points"], reverse=True)[:4]

    total_points = 0
    for comp_key, comp_data in top_comps:
        target_comps[comp_key]["counts"] = True
        total_points += comp_data["points"]

    json_data[target_id]["total_points"] = round(total_points, 2)
    print(f"✅ Successfully merged into {target_id}.")


def check_duplicate_athletes(json_data):
    name_map = _find_duplicate_athletes(json_data)

    # 2. Iterate through the map
    for key, ids in name_map.items():
        # Filter IDs to ensure they actually still exist in json_data
        # (This protects against cases where an ID was deleted in a previous merge)
        unique_ids = [cid for cid in ids if cid in json_data]

        if len(unique_ids) > 1:
                is_merge, target_id = _duplicate_athletes_user_interaction(key, unique_ids)

                if is_merge and target_id in unique_ids:
                    _merge_duplicate_athletes(unique_ids, target_id, json_data)
                else:
                    print("Cancelled merge. Skipping...")


def normalize_gender(gender):
    gender = gender.strip().upper()

    if gender == "W":   # normalize "W" to "F"
        gender = "F"

    while len(gender) > 1 or gender not in ["M", "F"]:
        print(f"\n⚠️ Invalid Gender found: '{gender}'")
        gender = input("Please enter a valid gender ('M' or 'F'): ").strip().upper()

    return gender


def normalize_nationality(nationality, info):
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
        print(f"\n⚠️ Invalid Nationality length: '{nationality}' for {info}")
        nationality = input("Please enter a valid 3-letter IOC country code (e.g., SUI): ").strip().upper()
        if nationality in replacements:
            nationality = replacements[nationality]

    return nationality


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

    except ValueError:
        print(f"⚠️ Unrecognized date format: '{date_str}'. Unable to extract year.")

    return 0

