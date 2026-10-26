# DevTrack (fixed local persistence)

## Run on macOS
Open Terminal in this folder, then run these commands one by one:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Important persistence fix
The SQLite database is now located at `devtrack.db` beside `database.py`, regardless of the directory from which you start the app. This prevents accidentally creating multiple empty databases in different folders.

Your current `devtrack.db` is included to preserve the data that was in the uploaded project. Make a backup copy before replacing your existing project folder.

## Notes
- Keep the terminal running while using the app.
- Stop the server with Ctrl+C.
- Do not type `Running on http://127.0.0.1:5000` into Terminal; it is a message printed by Flask.
- If you already have an older database with your own saved data, copy that database into this project folder as `devtrack.db` before starting the app.
