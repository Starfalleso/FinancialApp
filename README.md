
<img width="1913" height="1008" alt="fis" src="https://github.com/user-attachments/assets/9c3e15fb-3068-4b9b-98ac-f18d0f68c1dd" />


# Personal Finance Dashboard

Local desktop app built with PySide6 + SQLite.

## Run (Dev)

Using `uv` (recommended):

1. Install dependencies:
   - `uv sync`
2. Start app:
   - `uv run python app.py`

Using `pip` (alternative):

1. Install dependencies:
   - `pip install -e .`
2. Start app:
   - `python app.py`

## Data Storage Location

The app now stores its database in a per-user app data folder:

- Windows: `%LOCALAPPDATA%\PersonalFinanceDashboard\finance.db`
- macOS: `~/Library/Application Support/PersonalFinanceDashboard/finance.db`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/PersonalFinanceDashboard/finance.db`

Optional override:

- Set environment variable `FINANCEAPP_DATA_DIR` to a custom folder path.

Legacy migration:

- If a legacy `finance.db` exists in the project root and no user DB exists yet, it is copied to the new user data location on first launch.

## Public Build (Windows)

Use the included build script:

- `powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1`

Executable output:

- `dist\PersonalFinanceDashboard\PersonalFinanceDashboard.exe`

## Backup and Restore

Inside the app:

- Go to `Settings`
- Use `Backup Database` to save a `.db` snapshot
- Use `Restore Database` to load a backup on the current machine
