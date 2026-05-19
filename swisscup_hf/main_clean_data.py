from helpers.config import JSON_PATH
from helpers.utils import load_json, save_json

def clear_data(json_data: dict):
    for civil_id in json_data:
        json_data[civil_id]["competitions"] = {}
        json_data[civil_id]["total_points"] = 0


def main():
    # Load existing JSON data
    json_data = load_json(JSON_PATH)

    # Clear existing competition data and total points
    clear_data(json_data)

    # Save the data back to the JSON file
    save_json(json_data, JSON_PATH)


if __name__ == "__main__":
    main()