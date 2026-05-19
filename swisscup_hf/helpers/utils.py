
import json

def load_json(file_path: str) -> dict:
    data_json = {}
    try:
        with open(file_path, "r") as f:
            data_json = json.load(f)
    except FileNotFoundError:
        print("Competition JSON file does not exist yet.")
        data_json = {}
    return data_json


def save_json(data: dict, file_path: str):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)