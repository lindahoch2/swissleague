# Swisscup HF

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
