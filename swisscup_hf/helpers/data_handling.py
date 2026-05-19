import pandas as pd
from collections import defaultdict

def print_name_discrepancy(json_data, row, key):
      print(f"\nDiscrepancy found for civl_id {row['civl_id']}:")
      print(f"{key} in JSON: {json_data[str(row['civl_id'])][key]}, {key} in Excel: {row[key]}")


def check_civl_id_name_discrepancy(json_data, row):
      if json_data[str(row['civl_id'])]['name'] != row['name']:
        print_name_discrepancy(json_data, row, 'name')
      if json_data[str(row['civl_id'])]['first_name'] != row['first_name']:
        print_name_discrepancy(json_data, row, 'first_name')


def check_wing(json_data, row):
      if json_data[str(row['civl_id'])]['glider'] != row['glider']:
        if json_data[str(row['civl_id'])]['glider'] == "":
          print(f"\nUpdating empty glider for {row['civl_id']}")
          json_data[str(row['civl_id'])]['glider'] = row['glider']
        else:
          print(f"\nDiscrepancy in glider found for civl_id {row['civl_id']}:")
          print("old glider: ", json_data[str(row['civl_id'])]['glider'])
          print("new glider: ", row['glider'])


def add_points_to_data(df: pd.DataFrame, num_participants):
    # Formula: 100 - 100 * (rank - 1) / (num_participants -1)
    df['points'] = (100 - (100 * (df['rank'] - 1)) / (num_participants - 1)).clip(lower=1).round(2)

    return num_participants, df


def check_if_competition_already_exists(json_data, civil_id, competition_key):
    if competition_key in json_data[civil_id]["competitions"]:
      print(f"Competition {competition_key} already exists for civl_id {civil_id}")
      return True
    return False


def add_competition_data(json_data, data_row, competition_key):
    json_data[str(data_row['civl_id'])]["competitions"][competition_key] = {
        "rank": data_row['rank'],
        "points": data_row['points'],
        "counts": True
    }
    return json_data


def update_total_points(json_data, civil_id:str, new_points, new_comp_key):
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


def remove_athletes_data_from_comp_keys(athletes_comp_keys):
    exclude_keys = {'name', 'first_name', 'gender', 'total_points', 'nat', 'glider'}
    return [key for key in athletes_comp_keys if key not in exclude_keys]


def add_athlete_data(json_data, data_row):
    print()
    print(f"Adding athlete data for civl_id {data_row['civl_id']}")
    json_data[str(data_row['civl_id'])] = {
        "name": data_row['name'],
        "first_name": data_row['first_name'],
        "gender": data_row['gender'],
        "total_points": 0,
        "nat": data_row['nat'],
        "glider": data_row['glider'],
        "competitions": {}
    }
    return json_data


def add_data_to_json(json_data: dict, df: pd.DataFrame, competition_key: str):
    # add data to json
    for _, row in df.iterrows():
        # If fake civl_id, check if pilot already exists in database
        if "Z" in str(row['civl_id']):
            # Search in JSON for same last name
            for json_civl_id, athlete in json_data.items():
                if athlete['name'] == row['name']:
                    # Check if first name matches
                    if athlete['first_name'] == row['first_name']:
                        # Replace manual civl_id with real one
                        row['civl_id'] = json_civl_id
                        break

        # check data if civl_id already exists
        if str(row['civl_id']) in json_data:
            # check if there is name discrepancy for manual update
            check_civl_id_name_discrepancy(json_data, row)
            check_wing(json_data, row)

        else:
            # add athletes data
            json_data = add_athlete_data(json_data, row)

        # add the competition
        if not check_if_competition_already_exists(json_data, str(row['civl_id']), competition_key):
          json_data = add_competition_data(json_data, row, competition_key)
          json_data = update_total_points(json_data, str(row['civl_id']), row['points'], competition_key)

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


def find_duplicate_athletes(json_data):
    name_map = defaultdict(list)

    for civl_id, data in json_data.items():
        name = data.get('name', '').strip().lower()
        first_name = data.get('first_name', '').strip().lower()

        # Build both "name-first_name" and "first_name-name" as possible keys
        key1 = (name, first_name)
        key2 = (first_name, name)

        name_map[key1].append(civl_id)
        if key1 != key2:
            name_map[key2].append(civl_id)

    # Filter and print duplicates
    printed = set()
    for key, ids in name_map.items():
        unique_ids = set(ids)
        if len(unique_ids) > 1 and key not in printed:
            printed.add(key)
            print(f"Possible duplicate: {key[0].title()} {key[1].title()} found with CIVL IDs: {', '.join(sorted(unique_ids))}")


def normalize_gender(gender):
    gender = gender.strip().upper()

    if len(gender) > 1:
        print(f"Invalid Gender length. Gender: {gender}")

    if gender == "W":   # normalize "W" to "F"
        gender = "F"

    return gender


def normalize_nationality(nationality):
    nationality = nationality.strip().upper()

    replacements = {
        "CH": "SUI",
        "IT": "ITA",
        "UK": "GBR",
        "FR": "FRA",
        "F": "FRA",
        "NZ": "NZL",
        "D": "DEU",
        "AT": "AUT",
        "DK": "DNK",
        "UY": "URY",
        "DE": "DEU",
    }

    if nationality in replacements:
        nationality = replacements[nationality]

    if len(nationality) != 3:
        print(f"Invalid Nationality length. Nationality: {nationality}")

    return nationality

