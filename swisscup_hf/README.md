# Swisscup HF

This subproject handles the evaluation, data management, and PDF report generation for the Swisscup HF competitions.

## File Structure

- `main_swisscup_hf.py`: Main script to run the full evaluation or process specific competitions.
- `main_clean_data.py`: Utility to clear competition results from the JSON files while preserving athlete master data.
- `helpers/`: Contains helper modules for configuration (`config.py`), data processing (`data_handling.py`), PDF creation (`pdf.py`), and general logic (`utils.py`).
- `data/`: Directory holding the core JSON datasets (e.g., `swissleague_competitions_2026.json`, `swissleague_data_2026.json`), alongside directories for `competition_results`, `intermediate` data, and final `swisscup_results`.
- `requirements.txt`: Specific Python dependencies required for to run this evaluation pipeline.

## Setup and Usage

### Running the Evaluation:

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

4. **Update the paths in the config.py to your local data structure**

5. **Run the full script:**
   ```bash
   python main_swisscup_hf.py
   ```

5. **Run the script for specific competitions:**
   ```bash
   python main_swisscup_hf.py -c <comp_json_key1> <comp_json_key2>
   ```

### Utilities:

For clearing the competitions JSON but keeping the athlete info, you can run:
```bash
python main_clean_data.py
```