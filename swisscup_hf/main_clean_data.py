from helpers.config import JSON_PATH, COMPETITION_PATH
from helpers.utils import load_json, save_json

def clear_data(json_data: dict):
    for civil_id in json_data:
        json_data[civil_id]["competitions"] = {}
        json_data[civil_id]["total_points"] = 0

def remap_fake_ids(json_data: dict) -> dict:
    """
    Finds all fake IDs starting with 'ZZ', sorts them, and remaps them
    to a contiguous sequence without gaps.
    """
    # 1. Identify and sort the existing fake IDs (e.g., ['ZZ001', 'ZZ005', 'ZZ010'])
    fake_ids = sorted([cid for cid in json_data.keys() if str(cid).startswith("ZZ")])

    # 2. Create a mapping from the old fake ID to the new contiguous fake ID
    id_mapping = {}
    for index, old_id in enumerate(fake_ids, start=1):
        new_id = f"ZZ{index:03d}"
        id_mapping[old_id] = new_id

    # 3. Build and return a new dictionary with the remapped keys
    new_json_data = {}
    for cid, data in json_data.items():
        # If the ID is in our mapping, use the new ID, otherwise keep the real ID
        new_cid = id_mapping.get(cid, cid)
        new_json_data[new_cid] = data

    return new_json_data

def main():
    # Load existing JSON data
    json_data = load_json(JSON_PATH)

    # Remap the fake IDs to close any gaps before clearing
    json_data = remap_fake_ids(json_data)

    # Clear existing competition data and total points
    clear_data(json_data)

    # Save the data back to the JSON file
    save_json(json_data, JSON_PATH)

    comp_data = load_json(COMPETITION_PATH)

    # Reset num_participants to 0 for each competition
    for comp_key in comp_data:
        comp_data[comp_key]["num_participants"] = 0

    # Delete the excel file names from the competition data
    for comp_key in comp_data:
        if "filename" in comp_data[comp_key]:
            del comp_data[comp_key]["filename"]

    # Save the updated competition data back to the JSON file
    save_json(comp_data, COMPETITION_PATH)

if __name__ == "__main__":
    main()