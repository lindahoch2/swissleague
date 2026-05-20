# Swissleague

This repository contains tools and scripts for managing and evaluating data for leagues and competitions.

The project is structured into two main components:

- **[Swisscup HF](./swisscup_hf/)**: Scripts for evaluating and managing data for the Swisscup HF.
- **[XC Liga](./xc_liga/)**: Utilities for processing and matching Cross Country (XC) league signups against rank lists.

## Structure

### 1. Swisscup HF (`/swisscup_hf`)
Handles the evaluation, PDF generation, and data cleaning for the Swisscup HF competitions.
- `main_swisscup_hf.py`: Runs the full evaluation or processes specific competitions based on JSON data.
- `main_clean_data.py`: Utility to clear competition data while preserving athlete information.

For detailed setup and usage instructions, see the [Swisscup HF README](./swisscup_hf/README.md).

### 2. XC Liga (`/xc_liga`)
Utilities to load, compare, and modify Excel files (e.g., `liga_signups.xlsx`, `rangliste.xlsx`) using Pandas and OpenPyXL to determine league selections.
- `xc_ligue_selection.py`: The main utility script to load signups and results, match athletes, and output the summarized data.

## Getting Started

### Prerequisites
- Python 3.x
- [pandas](https://pandas.pydata.org/), [openpyxl](https://openpyxl.readthedocs.io/), [reportlab](https://www.reportlab.com/)

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/lindahoch2/swissleague.git
   cd swissleague
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv sl
   source sl/bin/activate
   ```

3. **Install dependencies:**
   Depending on which project you are working with, install the dependencies from the respective folder:
   ```bash
   # For Swisscup HF:
   pip install -r swisscup_hf/requirements.txt

   # For XC Liga:
   pip install -r xc_liga/requirements.txt
   ```

## License
This project is open-source and available under the [MIT License](LICENSE).