# XC Liga

This subproject contains utilities for processing and matching Cross Country (XC) league signups against competition rank lists. It utilizes `pandas` and `openpyxl` to extract, compare, and summarize data from Excel spreadsheets.

## Files Structure

- `xc_ligue_selection.py`: The main script that loads the signups and results, matches the athletes, and processes the summary columns.
- `requirements.txt`: The specific dependencies required for this subproject.
- `liga_signups.xlsx`: (Expected input file, not tracked in version control) Excel file containing the league signups.
- `rangliste.xlsx`: (Expected input file, not tracked in version control) Excel file containing the ranking lists.

## Setup

Assuming you have already set up a virtual environment from the root of the project, you can install the specific dependencies for this subproject by running:

```bash
cd xc_liga
pip install -r requirements.txt
```

## Usage

By default, the script expects both the `liga_signups.xlsx` and `rangliste.xlsx` files to be located in the same directory.

You can run the script via the command line:

```bash
python xc_ligue_selection.py
```
