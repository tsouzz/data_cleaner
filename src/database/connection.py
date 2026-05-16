import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path("media_cleaner.db")

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_tables():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            extension TEXT,
            size INTEGER NOT NULL,
            hash TEXT,
            created_at TEXT
        )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_size ON files(size)")

