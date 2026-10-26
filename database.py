"""SQLite persistence for DevTrack.

The database path is anchored to this file, not the shell's current directory.
This prevents the app from silently creating a second empty devtrack.db when
started from VS Code, another terminal directory, or a process manager.
"""
import os
import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DB_NAME = Path(os.environ.get("DEVTRACK_DB_PATH", PROJECT_DIR / "devtrack.db")).expanduser().resolve()


def get_db_connection():
    # timeout helps if the database is briefly busy; WAL improves local concurrent reads.
    conn = sqlite3.connect(str(DB_NAME), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    # Ensure a custom DB path's parent exists.
    DB_NAME.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            category TEXT NOT NULL DEFAULT 'Programming',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            language_id INTEGER NOT NULL,
            topic TEXT DEFAULT '',
            title TEXT NOT NULL DEFAULT 'Untitled Code',
            code TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES admin_users(id) ON DELETE CASCADE,
            FOREIGN KEY(language_id) REFERENCES languages(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coding_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            language_id INTEGER NOT NULL,
            elapsed_seconds INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES admin_users(id) ON DELETE CASCADE,
            FOREIGN KEY(language_id) REFERENCES languages(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            language_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            UNIQUE(user_id, language_id, topic),
            FOREIGN KEY(user_id) REFERENCES admin_users(id) ON DELETE CASCADE,
            FOREIGN KEY(language_id) REFERENCES languages(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flow_diagrams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT 'My Flowchart',
            diagram_data TEXT NOT NULL DEFAULT '[]',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, title),
            FOREIGN KEY(user_id) REFERENCES admin_users(id) ON DELETE CASCADE
        )
    """)

    default_languages = [
        ("C", "Programming"),
        ("C++", "Programming"),
        ("Python", "Programming"),
        ("Java", "Programming"),
        ("JavaScript", "Programming"),
        ("DSA", "Data Structures & Algorithms"),
    ]
    for name, category in default_languages:
        cursor.execute(
            "INSERT OR IGNORE INTO languages (name, category) VALUES (?, ?)",
            (name, category),
        )

    conn.commit()
    conn.close()
