import argparse
import pandas as pd
from helpers.config import *
from helpers.utils import load_json, save_json
from helpers.data_handling import (
    add_data_to_json,
    add_points_to_data,
    get_highest_fake_civil_id_already_in_use,
    normalize_glider_name,
    normalize_gender,
    normalize_nationality,
    check_duplicate_athletes,
    extract_year
)
from helpers.pdf import generate_pandas_data_frames, generate_single_pdf

def process_excel_files(json_keys: list, excel_files: list, results_path: str, json_data: dict, competition_json: dict):
    for competition_key, excel_file in zip(json_keys, excel_files):
        # Load the Excel file
        excel_path = f"{results_path}/{excel_file}"
        print(f"Processing {excel_path}...")
        df = pd.read_excel(excel_path)

        # Catch different column naming for birthdate and rename to a consistent name
        df = df.rename(columns={'Birthdate': 'Birth Date'})

        # Select only the necessary columns and rename for consistency
        df = df[['Rank', 'First Name', 'Last Name', 'Gender', 'CIVL ID', 'Nat', 'Glider', 'Birth Date']]
        df.columns = ['rank', 'first_name', 'name', 'gender', 'civl_id', 'nat', 'glider', 'birth_day']

        df['birth_year'] = df['birth_day'].apply(extract_year)

        # Evaluating the Points received based on ranking
        # Fallback to len(df) if the competition key or "num_participants" is missing
        num_participants = competition_json.get(competition_key, {}).get("num_participants")

        if not num_participants or num_participants == 0:
            num_participants = len(df)
            print(f"Warning: 'num_participants' not found for {competition_key}. Falling back to Excel row count: {num_participants}")

            if competition_key not in competition_json:
                competition_json[competition_key] = {
                    "title": competition_key.capitalize(),
                    "num_participants": num_participants,
                    "physical": False
                }
                print(f"Added new entry for {competition_key} in competition JSON with 'num_participants': {num_participants}.")
            competition_json[competition_key]["num_participants"] = num_participants
            save_json(competition_json, COMPETITION_PATH)
            print(f"Updated 'num_participants' for {competition_key} in competition JSON.")

        num_part, df = add_points_to_data(df, num_participants)

        # removing possible blanc spaces around civil id
        df['civl_id'] = df['civl_id'].astype(str).str.strip()

        fake_id_counter = get_highest_fake_civil_id_already_in_use(json_data)

        def replace_zero_with_fake(cid):
            global fake_id_counter
            if cid == "0":
                new_cid = f"ZZ{fake_id_counter:03d}"  # e.g. ZZ001, ZZ002
                fake_id_counter += 1
                return new_cid
            return cid

        # Replace civil id's "0" with a fake ID
        df['civl_id'] = df['civl_id'].apply(replace_zero_with_fake)

        # remove trailing blank spaces
        df['name'] = df['name'].str.strip().str.title()
        df['first_name'] = df['first_name'].str.strip().str.title()
        df['glider'] = df['glider'].fillna("").str.strip()

        # add data to json
        json_data = add_data_to_json(json_data, df, competition_key)


def data_cleaning(json_data: dict):
    for athlete in json_data.keys():
        athlete_info = f"{json_data[athlete]}: {json_data[athlete]['name']} {json_data[athlete]['first_name']}"
        json_data[athlete]["glider"] = normalize_glider_name(json_data[athlete]["glider"])
        json_data[athlete]["gender"] = normalize_gender(json_data[athlete]["gender"])
        json_data[athlete]["nat"] = normalize_nationality(json_data[athlete]["nat"], athlete_info)

    check_duplicate_athletes(json_data)


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

    # Load existing JSON data
    data_json = load_json(JSON_PATH)

    # Load competition JSON data
    competition_json = load_json(COMPETITION_PATH)

    # Process each Excel file and update JSON data
    process_excel_files(keys_to_process, files_to_process, RESULTS_DIR, data_json, competition_json)

    # Clean the data
    data_cleaning(data_json)

    last_key = ""
    if keys_to_process:
        last_key = keys_to_process[-1]

    # Generate PDF report
    generate_pdfs(competition_json, data_json, last_key)

    # Save the updated JSON data
    save_json(data_json, JSON_PATH)

    # Save the additional Intermediate Results
    additional_json_path = INTERMEDIATE_DIR / f"swissleague_data_2026_{last_key}.json"
    save_json(data_json, additional_json_path)
    print(f"Additional JSON saved to: {additional_json_path}")

if __name__ == "__main__":
    main()