import argparse
import pandas as pd
from helpers.config import *
from helpers.utils import load_json, save_json
from helpers.resolvers import CLIConflictResolver
from helpers.models import Athlete
from helpers.data_handling import (
    add_data_to_json,
    add_points_to_data,
    get_highest_fake_civil_id_already_in_use,
    replace_zero_with_fake,
    data_cleaning,
    extract_year,
    renaming_pandas_columns
)
from helpers.pdf import generate_pandas_data_frames, generate_single_pdf

def read_and_standardize_excel(results_path, excel_file):
    df = pd.read_excel(f"{results_path}/{excel_file}")
    df = renaming_pandas_columns(df)
    df = df[['Rank', 'First Name', 'Last Name', 'Gender', 'CIVL ID', 'Nat', 'Glider', 'Birth Date']]
    df.columns = ['rank', 'first_name', 'name', 'gender', 'civl_id', 'nat', 'glider', 'birth_day']
    df['birth_year'] = df['birth_day'].apply(extract_year)
    return df

def get_or_update_participants(comp_key, competition_json, df_len):
    num_participants = competition_json.get(comp_key, {}).get("num_participants")
    if not num_participants or num_participants == 0:
        num_participants = df_len
        if comp_key not in competition_json:
            competition_json[comp_key] = {
                "title": comp_key.capitalize(),
                "num_participants": num_participants,
                "physical": False
            }
        else:
            competition_json[comp_key]["num_participants"] = num_participants
        save_json(competition_json, COMPETITION_PATH)
    return num_participants

def clean_dataframe_text(df):
    df['civl_id'] = df['civl_id'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df['name'] = df['name'].str.strip().str.title()
    df['first_name'] = df['first_name'].str.strip().str.title()
    df['glider'] = df['glider'].fillna("").str.strip()
    return df

def process_excel_files(json_keys, excel_files, results_path, athletes_dict, competition_json, resolver):
    fake_id_counter = get_highest_fake_civil_id_already_in_use(athletes_dict)

    for comp_key, excel_file in zip(json_keys, excel_files):
        print(f"Processing {excel_file}...")

        # 1. Extract
        df = read_and_standardize_excel(results_path, excel_file)

        # 2. Transform
        num_participants = get_or_update_participants(comp_key, competition_json, len(df))
        _, df = add_points_to_data(df, num_participants)
        df = clean_dataframe_text(df)

        # Inject fake IDs
        df['civl_id'] = df['civl_id'].apply(lambda cid: replace_zero_with_fake(cid, fake_id_counter))
        fake_id_counter = get_highest_fake_civil_id_already_in_use(athletes_dict) # Update counter

        # 3. Load
        add_data_to_json(athletes_dict, df, comp_key, resolver)

def generate_pdfs(competition_json: dict, json_data: dict, comp_key: str):
    all_competitions = competition_json.keys()

    df_female, df_male, df_u26, df_overall = generate_pandas_data_frames(json_data, all_competitions)

    # Filter out rows where total_points is 0
    df_female = df_female[df_female["total_points"] != 0]
    df_male = df_male[df_male["total_points"] != 0]
    df_overall = df_overall[df_overall["total_points"] != 0]
    df_u26 = df_u26[df_u26["total_points"] != 0]

    # Sort by total points descending
    df_female.sort_values("total_points", ascending=False, inplace=True)
    df_male.sort_values("total_points", ascending=False, inplace=True)
    df_overall.sort_values("total_points", ascending=False, inplace=True)
    df_u26.sort_values("total_points", ascending=False, inplace=True)

    # generate the PDFs
    generate_single_pdf(json_data, competition_json, df_female, WOMEN_TITLE, OUTPUT_DIR / f"{FILE_PREFIX}_{comp_key}_female.pdf")
    generate_single_pdf(json_data, competition_json, df_male, MEN_TITLE, OUTPUT_DIR / f"{FILE_PREFIX}_{comp_key}_male.pdf")
    generate_single_pdf(json_data, competition_json, df_overall, OVERALL_TITLE, OUTPUT_DIR / f"{FILE_PREFIX}_{comp_key}_overall.pdf")
    generate_single_pdf(json_data, competition_json, df_u26, JUNIOR_TITLE, OUTPUT_DIR / f"{FILE_PREFIX}_{comp_key}_junior.pdf")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process Swissleague Hike and Fly results.")
    parser.add_argument(
        '-c', '--comps',
        nargs='+',
        help="List of competition keys to evaluate (e.g., -c jhf eiger airtour). If omitted, runs all."
    )
    args = parser.parse_args()

    print(f"Base Directory: {BASE_DIR}")
    print(f"Data Directory: {DATA_DIR}")

    # Determine which competitions to run
    selected_keys = args.comps if args.comps else JSON_KEYS

    keys_to_process = []
    files_to_process = []

    # Map the selected keys to their corresponding excel files
    for key, file in zip(JSON_KEYS, EXCEL_FILES):
        if key in selected_keys:
            keys_to_process.append(key)
            files_to_process.append(file)

    # Validate inputs to catch any typos in the command line
    invalid_keys = set(selected_keys) - set(JSON_KEYS)
    if invalid_keys:
        print(f"\nWarning: The following keys are invalid and will be ignored: {', '.join(invalid_keys)}")
        print(f"Valid keys are: {', '.join(JSON_KEYS)}\n")

    if not keys_to_process:
        print("No valid competitions selected. Exiting.")
        return

    print(f"Evaluating competitions: {', '.join(keys_to_process)}")

    # Load existing JSON data and convert to Athlete objects
    raw_json = load_json(JSON_PATH)
    athletes_dict = {civl_id: Athlete.from_dict(civl_id, data) for civl_id, data in raw_json.items()}

    # Load competition JSON data
    competition_json = load_json(COMPETITION_PATH)
    resolver = CLIConflictResolver()

    # Process and Clean
    process_excel_files(keys_to_process, files_to_process, RESULTS_DIR, athletes_dict, competition_json, resolver)
    data_cleaning(athletes_dict, resolver)

    # Save back to raw dictionaries for JSON serialization
    updated_raw_json = {civl_id: ath.to_dict() for civl_id, ath in athletes_dict.items()}
    save_json(updated_raw_json, JSON_PATH)

    # Save the additional Intermediate Results
    last_key = ""
    if keys_to_process:
        last_key = keys_to_process[-1]
    additional_json_path = INTERMEDIATE_DIR / f"swissleague_data_2026_{last_key}.json"
    save_json(updated_raw_json, additional_json_path)
    print(f"Additional JSON saved to: {additional_json_path}")

    # Generate PDFs
    if keys_to_process:
        generate_pdfs(competition_json, updated_raw_json, keys_to_process[-1])

if __name__ == "__main__":
    main()