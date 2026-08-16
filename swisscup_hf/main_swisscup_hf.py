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
    renaming_pandas_columns,
    clean_dataframe_text
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

def process_excel_files(json_keys, excel_files, results_path, athletes_dict, competition_json, resolver):
    fake_id_counter = get_highest_fake_civil_id_already_in_use(athletes_dict)

    for comp_key, excel_file in zip(json_keys, excel_files):
        print(f"Processing {excel_file} (Key: {comp_key})...")

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


def get_or_register_competition_key(filename: str, competition_json: dict, resolver: CLIConflictResolver) -> str:
    """Finds the competition key for a file, prompting the user if it's unknown."""
    # 1. Exact Match
    for key, data in competition_json.items():
        if data.get("filename") == filename:
            return key

    # 2. Ask user via Resolver
    similar_keys = sorted(
        [k for k in competition_json.keys() if k.lower() in filename.lower()], 
        key=len, 
        reverse=True
    )
    comp_key, new_config = resolver.resolve_unknown_competition(filename, similar_keys, competition_json)

    # 3. Update Configuration if a key was chosen
    if comp_key:
        if new_config:
            competition_json[comp_key] = new_config
        competition_json[comp_key]["filename"] = filename
        save_json(competition_json, COMPETITION_PATH)

    return comp_key


def should_process_competition(comp_key: str, competition_json: dict, args: argparse.Namespace) -> bool:
    """Determines if a competition should be processed based on args and current state."""
    if args.comps and comp_key not in args.comps:
        return False

    is_explicitly_requested = args.comps and comp_key in args.comps
    is_processed = competition_json.get(comp_key, {}).get("num_participants", 0) > 0

    if is_processed and not (args.force or is_explicitly_requested):
        return False

    return True


def discover_files_to_process(available_files: list, competition_json: dict, args: argparse.Namespace, resolver: CLIConflictResolver) -> tuple[list, list]:
    """Iterates through files and filters down to the ones that need processing."""
    keys_to_process, files_to_process = [], []

    for filepath in sorted(available_files):
        filename = filepath.name
        comp_key = get_or_register_competition_key(filename, competition_json, resolver)

        if not comp_key:
            print(f"⏭️  Skipping '{filename}'.")
            continue

        if not should_process_competition(comp_key, competition_json, args):
            print(f"⏩ Skipping '{filename}' (already processed). Use --force to reprocess.")
            continue

        keys_to_process.append(comp_key)
        files_to_process.append(filename)

    return keys_to_process, files_to_process


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process Swissleague Hike and Fly results.")
    parser.add_argument('-c', '--comps', nargs='+', help="List of competition keys to explicitly evaluate (e.g., -c jhf eiger).")
    parser.add_argument('-f', '--force', action='store_true', help="Force reprocessing of all competitions.")
    return parser.parse_args()


def main():
    args = parse_arguments()
    print(f"Base Directory: {BASE_DIR}\nData Directory: {DATA_DIR}")

    competition_json = load_json(COMPETITION_PATH)
    resolver = CLIConflictResolver()

    # 1. Discover and Filter Files
    available_files = list(RESULTS_DIR.glob("*.xlsx"))
    if not available_files:
        print(f"No Excel files found in {RESULTS_DIR}. Exiting.")
        return

    keys_to_process, files_to_process = discover_files_to_process(
        available_files, competition_json, args, resolver
    )

    if not keys_to_process:
        print("\nNo valid or new competitions selected. Exiting.")
        return

    print(f"\nEvaluating competitions: {', '.join(keys_to_process)}")

    # 2. Load Base Data
    raw_json = load_json(JSON_PATH)
    athletes_dict = {civl_id: Athlete.from_dict(civl_id, data) for civl_id, data in raw_json.items()}

    # 3. Process and Clean
    process_excel_files(keys_to_process, files_to_process, RESULTS_DIR, athletes_dict, competition_json, resolver)
    data_cleaning(athletes_dict, resolver)

    # 4. Save and Generate Output
    updated_raw_json = {civl_id: ath.to_dict() for civl_id, ath in athletes_dict.items()}
    save_json(updated_raw_json, JSON_PATH)

    last_key = keys_to_process[-1]
    additional_json_path = INTERMEDIATE_DIR / f"swissleague_data_2026_{last_key}.json"
    save_json(updated_raw_json, additional_json_path)
    print(f"Additional JSON saved to: {additional_json_path}")

    generate_pdfs(competition_json, updated_raw_json, last_key)


if __name__ == "__main__":
    main()