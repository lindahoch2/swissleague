"""
CIVL ID Auto-Filler Tool

This script processes an Excel file containing athlete data, looking for missing 
CIVL IDs. It cross-references the names against a master JSON database of athletes.
- Exact name matches (including swapped first/last names) are filled automatically.
- Near matches (typos, alternate spellings) trigger an interactive CLI prompt 
  where the user can select the correct athlete.

Usage:
    python fill_civl_ids.py -e input.xlsx -j master_db.json -o output.xlsx

Arguments:
    -e, --excel: Path to the target Excel file.
    -j, --json:  Path to the master JSON database file.
    -o, --output (Optional): Path to save the updated Excel file. If omitted, 
                 the original file is overwritten.
"""

import argparse
import pandas as pd
import difflib
import json
import os

def load_json(filepath):
    """
    Loads and parses a JSON file.

    Args:
        filepath (str): The path to the JSON file.

    Returns:
        dict: The parsed JSON data.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def _find_athlete_in_json(first_name, last_name, json_data):
    """
    Searches for an athlete in the JSON data using exact and fuzzy matching.

    Args:
        first_name (str): The athlete's first name from the Excel file.
        last_name (str): The athlete's last name from the Excel file.
        json_data (dict): The master database where keys are CIVL IDs and
                          values are dicts containing 'first_name' and 'name'.

    Returns:
        tuple: (result, is_exact_match)
            - If exact match: (civl_id (str), True)
            - If fuzzy match: (list_of_possible_civl_ids (list), False)
            - If no match: (None, False)
    """
    fn = str(first_name).strip().lower()
    ln = str(last_name).strip().lower()
    full_name = f"{fn} {ln}"
    full_name_rev = f"{ln} {fn}" # Handle swapped first/last names

    name_to_civl = {}

    # 1. Check for exact matches and build mapping for fuzzy search
    for civl, data in json_data.items():
        j_fn = str(data.get('first_name', '')).strip().lower()
        j_ln = str(data.get('name', '')).strip().lower()

        # Exact match (direct or swapped)
        if (fn == j_fn and ln == j_ln) or (fn == j_ln and ln == j_fn):
            return civl, True

        # Build mapping for difflib (store both regular and swapped orders)
        name_to_civl[f"{j_fn} {j_ln}"] = civl
        name_to_civl[f"{j_ln} {j_fn}"] = civl

    # 2. Fuzzy search for similar names (typos, etc.)
    # cutoff=0.7 means names must be 70% similar to be suggested
    matches = difflib.get_close_matches(full_name, name_to_civl.keys(), n=4, cutoff=0.7)

    # Fallback: try fuzzy matching against the reversed name
    if not matches:
        matches = difflib.get_close_matches(full_name_rev, name_to_civl.keys(), n=4, cutoff=0.7)

    if matches:
        # Deduplicate CIVL IDs from the matches (in case both normal and reversed matched)
        unique_civls = list(set([name_to_civl[m] for m in matches]))
        return unique_civls, False

    return None, False

def _user_interaction_similar_name(excel_name, candidates, json_data):
    """
    Prompts the user via the CLI to resolve a fuzzy name match.

    Args:
        excel_name (str): The original name from the Excel file.
        candidates (list): A list of potential CIVL IDs found via fuzzy matching.
        json_data (dict): The master database to look up candidate display names.

    Returns:
        str or None: The confirmed CIVL ID chosen by the user, or None if skipped.
    """
    print(f"\n🔍 Missing CIVL ID for Excel athlete: '{excel_name.title()}'")
    print("Found similar names in JSON database:")

    for i, civl in enumerate(candidates):
        j_fn = json_data[civl].get('first_name', '').title()
        j_ln = json_data[civl].get('name', '').title()
        print(f"  [{i+1}] {j_fn} {j_ln} (CIVL ID: {civl})")

    print(f"  [0] None of the above (Skip)")

    while True:
        choice = input(f"Select the correct athlete [0-{len(candidates)}]: ").strip()
        if choice.isdigit():
            choice_idx = int(choice)
            if choice_idx == 0:
                return None
            elif 1 <= choice_idx <= len(candidates):
                return candidates[choice_idx - 1]
        print("Invalid input. Please enter a valid number.")

def process_missing_civl_ids(excel_path, json_path, output_path=None):
    """
    Main pipeline: loads files, iterates through missing IDs, resolves them, 
    and saves the updated Excel file.

    Args:
        excel_path (str): Path to the input Excel file.
        json_path (str): Path to the master JSON database.
        output_path (str, optional): Path to save the output. Defaults to overwriting 
                                     the input Excel file.
    """
    if not output_path:
        # Default to overwriting the original file
        output_path = excel_path

    print(f"Loading JSON from {json_path}...")
    json_data = load_json(json_path)

    print(f"Loading Excel from {excel_path}...")
    df = pd.read_excel(excel_path)

    # Detect column names gracefully using partial string matching
    civl_col = next((col for col in df.columns if 'civl' in col.lower()), None)
    first_name_col = next((col for col in df.columns if 'first' in col.lower()), None)
    last_name_col = next((col for col in df.columns if 'last' in col.lower() or col.lower() == 'name'), None)

    if not all([civl_col, first_name_col, last_name_col]):
        print("❌ Error: Could not automatically detect necessary columns (CIVL ID, First Name, Last Name).")
        print(f"Found columns: {list(df.columns)}")
        return

    # Ensure the CIVL column can accept mixed types (strings/ints)
    df[civl_col] = df[civl_col].astype(object)

    updates_count = 0

    for index, row in df.iterrows():
        civl_val = row[civl_col]

        # Check if CIVL ID is empty, NaN, or explicitly "0"
        if pd.isna(civl_val) or str(civl_val).strip() in ['', '0', '0.0']:
            fn = row[first_name_col]
            ln = row[last_name_col]

            # Skip entirely blank rows
            if pd.isna(fn) and pd.isna(ln):
                continue

            match_result, is_exact = _find_athlete_in_json(fn, ln, json_data)

            if is_exact:
                print(f"✅ Exact match auto-filled for '{fn} {ln}': {match_result}")
                # Convert to integer if it's a pure number to avoid Excel's single quote formatting warning
                clean_id = int(match_result) if str(match_result).isdigit() else match_result
                df.at[index, civl_col] = clean_id
                updates_count += 1

            elif match_result:
                # Fuzzy matches found -> Ask user for confirmation
                excel_name = f"{fn} {ln}"
                chosen_civl = _user_interaction_similar_name(excel_name, match_result, json_data)

                if chosen_civl:
                    print(f"✅ User confirmed match. Updating to: {chosen_civl}")
                    clean_id = int(chosen_civl) if str(chosen_civl).isdigit() else chosen_civl
                    df.at[index, civl_col] = clean_id
                    updates_count += 1
                else:
                    print("⏭️ Skipped.")

    # Only save if modifications were actually made
    if updates_count > 0:
        print(f"\n💾 Saving {updates_count} updates to {output_path}...")
        df.to_excel(output_path, index=False)
        print("Done!")
    else:
        print("\n✨ No missing CIVL IDs needed updating.")

def main():
    """
    Parses command-line arguments and triggers the main processing pipeline.
    """
    parser = argparse.ArgumentParser(description="Fill missing CIVL IDs in Excel by checking JSON data.")
    parser.add_argument('-e', '--excel', required=True, help="Path to the Excel file to process.")
    parser.add_argument('-j', '--json', required=True, help="Path to the master JSON file.")
    parser.add_argument('-o', '--output', required=False, help="Path to save the updated Excel file (overwrites original if omitted).")

    args = parser.parse_args()

    # Validate file existence before starting the pipeline
    if not os.path.exists(args.excel):
        print(f"❌ Excel file not found: {args.excel}")
        return

    if not os.path.exists(args.json):
        print(f"❌ JSON file not found: {args.json}")
        return

    process_missing_civl_ids(args.excel, args.json, args.output)

if __name__ == "__main__":
    main()