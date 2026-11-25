# Survey Result Explorer

A modern, local-first Python desktop application for survey response entry, validation, cleaning, searching, analytics, charts, imports, and exports.


## Features
- Modern desktop UI (PySide6) with Dashboard, Records, Add Response, Search & Filter, Analytics, and Reports pages
- Add, edit, and delete survey responses; respondent, category, 0–100 rating, date, and comments
- Defensive validation for required fields, numeric rating bounds, ISO date, and field lengths
- CSV and JSON local persistence, with automatic JSON backups and audit log
- Search across respondents, categories, comments, rating, and date; category and date filters
- Cleaning: trim text, validate entries, remove duplicate respondent/category/date combinations, report invalid rows
- Analytics: totals, average, category counts, high/low ratings, monthly average trend, generated insights
- Bar, pie, and line chart; save category chart as PNG
- CSV bulk import with per-row error details
- Export records as CSV/JSON; summary as Markdown/TXT
- Low-rating threshold alert
- 40 sample responses generated for first launch/demo

## Run on Windows 10/11
1. Install Python 3.10 or newer from https://www.python.org/downloads/ and ensure Python is added to PATH.
2. Extract the project ZIP.
3. Double-click `launch_windows.bat`. It creates the virtual environment, installs dependencies, and launches the app.

Or manually:
```bash
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
To skip the 40-record demo dataset on first launch, run `python main.py --empty`.

## Data location
- `data/surveys.json` — main structured record store
- `data/surveys.csv` — CSV mirror
- `data/backups/` — previous JSON snapshots
- `data/audit.log` — local actions log

The first launch seeds 40 demonstration responses if no records exist. Use `python main.py --empty` to bypass demo seeding on an empty store and start with no records.


## Import CSV columns
Required columns: `respondent`, `category`, `rating`, `response_date` (ISO date `YYYY-MM-DD`). Optional: `id`, `comments`. Import accepts validated rows and reports rejected row numbers.

## Export
From Reports & Export, select CSV, JSON, Markdown summary, TXT report, PNG chart, or Import CSV.


## Project layout
```
Survey_Result_Explorer/
├── main.py
├── requirements.txt
├── launch_windows.bat
├── app/
│   ├── core/       # models, validation, storage, cleaning, search, analytics, export
│   └── ui/        # desktop GUI
├── data/          # generated on launch
├── tests/         # unit tests
└── assets/
```
