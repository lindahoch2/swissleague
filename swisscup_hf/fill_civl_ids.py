"""
CIVL ID Auto-Filler Tool

This script processes an Excel file containing athlete data, looking for missing
CIVL IDs. It cross-references the names against a master JSON database of athletes.
- Exact name matches (including swapped first/last names) are filled automatically.
- Near matches (typos, alternate spellings) trigger an interactive CLI prompt
  where the user can select the correct athlete.
"""

import argparse
import pandas as pd
import difflib
import json
import os

# ==========================================
# Data Loading & Preparation
# ==========================================

def load_json(filepath):
    """Loads and parses a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_name_lookup(json_data):
    """
    Pre-computes a lookup dictionary mapping 'first last' and 'last first'
    to the CIVL ID. This prevents iterating the JSON for every Excel row.
    """
    lookup = {}
    for civl, data in json_data.items():
        fn = str(data.get('first_name', '')).strip().lower()
        ln = str(data.get('name', '')).strip().lower()

        lookup[f"{fn} {ln}"] = civl
        lookup[f"{ln} {fn}"] = civl
    return lookup

# ==========================================
# Matching Logic
# ==========================================

def get_exact_match(full_name, full_name_rev, name_lookup):
    """Checks if the exact name exists in the lookup dictionary."""
    return name_lookup.get(full_name) or name_lookup.get(full_name_rev)

def get_fuzzy_matches(full_name, full_name_rev, name_lookup, cutoff=0.7):
    """Finds close spelling matches in the lookup dictionary."""
    candidates = list(name_lookup.keys())

    matches = difflib.get_close_matches(full_name, candidates, n=4, cutoff=cutoff)
    if not matches:
        matches = difflib.get_close_matches(full_name_rev, candidates, n=4, cutoff=cutoff)

    if matches:
        return list(set(name_lookup[m] for m in matches))
    return []

# ==========================================
# DataFrame Utilities
# ==========================================

def detect_columns(df):
    """Detects necessary columns gracefully using partial string matching."""
    civl_col = next((c for c in df.columns if 'civl' in c.lower()), None)
    fn_col = next((c for c in df.columns if 'first' in c.lower()), None)
    ln_col = next((c for c in df.columns if 'last' in c.lower() or c.lower() == 'name'), None)
    return civl_col, fn_col, ln_col

def is_missing_id(civl_val):
    """Determines if a CIVL ID cell is considered missing or blank."""
    return pd.isna(civl_val) or str(civl_val).strip() in ['', '0', '0.0']

def format_id(civl_id):
    """Formats the ID as an integer if it's a pure number to avoid Excel warnings."""
    return int(civl_id) if str(civl_id).isdigit() else civl_id

# ==========================================
# User Interaction
# ==========================================

def prompt_user_for_match(excel_name, candidates, json_data):
    """Prompts the user via the CLI to resolve a fuzzy name match."""
    print(f"\n🔍 Missing CIVL ID for Excel athlete: '{excel_name.title()}'")
    print("Found similar names in JSON database:")

    for i, civl in enumerate(candidates):
        j_fn = json_data[civl].get('first_name', '').title()
        j_ln = json_data[civl].get('name', '').title()
        print(f"  [{i+1}] {j_fn} {j_ln} (CIVL ID: {civl})")

    print(f"  [0] None of the above (Skip)")

    while True:
        choice = input(f"Select the correct athlete [0-{len(candidates)}]: ").strip()
        if choice.isdigit() and 0 <= int(choice) <= len(candidates):
            choice_idx = int(choice)
            return candidates[choice_idx - 1] if choice_idx > 0 else None
        print("Invalid input. Please enter a valid number.")

# ==========================================
# Main Processing Pipeline
# ==========================================

def process_dataframe(df, json_data):
    """Iterates through the dataframe, applying matching logic to missing records."""
    civl_col, fn_col, ln_col = detect_columns(df)

    if not all([civl_col, fn_col, ln_col]):
        raise ValueError(f"Could not detect necessary columns. Found: {list(df.columns)}")

    df[civl_col] = df[civl_col].astype(object)
    name_lookup = build_name_lookup(json_data)
    updates_count = 0

    for index, row in df.iterrows():
        if not is_missing_id(row[civl_col]):
            continue

        fn = str(row[fn_col]).strip().lower()
        ln = str(row[ln_col]).strip().lower()

        if fn == 'nan' and ln == 'nan':
            continue

        full_name, full_name_rev = f"{fn} {ln}", f"{ln} {fn}"

        # 1. Try Exact Match
        exact_match = get_exact_match(full_name, full_name_rev, name_lookup)
        if exact_match:
            print(f"✅ Exact match auto-filled for '{fn} {ln}': {exact_match}")
            df.at[index, civl_col] = format_id(exact_match)
            updates_count += 1
            continue

        # 2. Try Fuzzy Match
        fuzzy_matches = get_fuzzy_matches(full_name, full_name_rev, name_lookup)
        if fuzzy_matches:
            chosen_civl = prompt_user_for_match(full_name, fuzzy_matches, json_data)
            if chosen_civl:
                print(f"✅ User confirmed match. Updating to: {chosen_civl}")
                df.at[index, civl_col] = format_id(chosen_civl)
                updates_count += 1
            else:
                print("⏭️ Skipped.")

    return df, updates_count

def run_pipeline(excel_path, json_path, output_path=None):
    """Coordinates file loading, processing, and saving."""
    output_path = output_path or excel_path

    print("Loading data...")
    json_data = load_json(json_path)
    df = pd.read_excel(excel_path)

    try:
        df, updates_count = process_dataframe(df, json_data)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    if updates_count > 0:
        print(f"\n💾 Saving {updates_count} updates to {output_path}...")
        df.to_excel(output_path, index=False)
        print("Done!")
    else:
        print("\n✨ No missing CIVL IDs needed updating.")

def main():
    parser = argparse.ArgumentParser(description="Fill missing CIVL IDs in Excel by checking JSON data.")
    parser.add_argument('-e', '--excel', required=True, help="Path to the Excel file to process.")
    parser.add_argument('-j', '--json', required=True, help="Path to the master JSON file.")
    parser.add_argument('-o', '--output', required=False, help="Path to save the updated Excel file.")
    args = parser.parse_args()

    if not os.path.exists(args.excel):
        print(f"❌ Excel file not found: {args.excel}")
        return
    if not os.path.exists(args.json):
        print(f"❌ JSON file not found: {args.json}")
        return

    run_pipeline(args.excel, args.json, args.output)

if __name__ == "__main__":
    main()