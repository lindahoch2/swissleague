# Swisscup HF

This subproject handles the evaluation, data management, and PDF report generation for the Swisscup HF competitions.

## File Structure

- `main_swisscup_hf.py`: Main script to run the evaluation. It automatically scans for new competition files and processes them.
- `main_clean_data.py`: Utility to clear competition results from the JSON files while preserving athlete master data.
- `fill_civl_ids.py`: Utility to automatically fill missing CIVL IDs in competition Excel files by cross-referencing the JSON database.
- `helpers/`: Contains helper modules for configuration (`config.py`), data processing (`data_handling.py`), PDF creation (`pdf.py`), and general logic (`utils.py`).
- `data/`: Directory holding the core JSON datasets (e.g., `swissleague_competitions_2026.json`, `swissleague_data_2026.json`).
  - `competition_results/`: **Place your Excel (`.xlsx`) result files here.**
  - `intermediate/`: Stores intermediate JSON backups during processing.
  - `swisscup_results/`: The output folder where the final generated PDF reports are saved.
- `requirements.txt`: Specific Python dependencies required to run this evaluation pipeline.

## Setup

1. **Create a virtual environment:**
   ```bash
   python3 -m venv slhf
   ```

2. **Activate the environment:**
   ```bash
   source slhf/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify configuration (Optional):** Ensure the paths in `helpers/config.py` align with your local data structure if you have modified the default folder layout.

## How to Use

### 1. Adding Competition Data
Simply place your downloaded or exported `.xlsx` competition result files into the `data/competition_results/` folder.
*(Note: If your Excel files are missing athlete CIVL IDs, we recommend running the `fill_civl_ids.py` utility described in the Utilities section before running the evaluation).*

### 2. Running the Evaluation
The script will automatically discover all `.xlsx` files in the results directory, check if they are already in your database, and process them.

**To run the standard evaluation:**
```bash
python main_swisscup_hf.py
```

* **Interactive Prompts:** If the script finds a new Excel file it doesn't recognize, it will prompt you in the terminal to register it (create a competition key). It will also prompt you to resolve name discrepancies, glider changes, or duplicate athletes.
* **Smart Skipping:** By default, the script skips files that have already been fully processed (where participant count > 0) to save time and prevent duplicate work.

### 3. Advanced Execution Flags

**Force reprocessing:**
If you need to re-evaluate competitions that were already processed (e.g., if you corrected a mistake in the Excel file), use the `--force` (or `-f`) flag.
```bash
python main_swisscup_hf.py --force
```

**Evaluate specific competitions:**
If you only want to process one or more specific competitions and ignore the rest, use the `--comps` (or `-c`) flag followed by the competition keys.
```bash
python main_swisscup_hf.py -c <comp_json_key1> <comp_json_key2>
```

## Utilities

### Cleaning Data (`main_clean_data.py`)
For clearing the competitions out of your JSON database while **keeping** the athlete master data (names, IDs, birth years), you can run:
```bash
python main_clean_data.py
```

### CIVL ID Auto-Filler (`fill_civl_ids.py`)
If your competition Excel files are missing athlete CIVL IDs, use this tool to automatically populate them by cross-referencing names against your master JSON database.

- **Exact Matches:** Names matching perfectly (including swapped first/last names) are filled automatically.
- **Near Matches:** Typos or alternate spellings trigger an interactive CLI prompt so you can manually select the correct athlete.

**Usage:**
```bash
python fill_civl_ids.py -e data/competition_results/input.xlsx -j data/swissleague_data_2026.json
```

**Arguments:**
- `-e, --excel`: Path to the target Excel file.
- `-j, --json`: Path to the master JSON database file.
- `-o, --output` *(Optional)*: Path to save the updated Excel file. If omitted, the original file is overwritten.