import sqlite3
import os

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
DB_PATH = "/tmp/database.db" if os.environ.get("VERCEL") else "database.db"

def initialize_schema():
    print("Initializing SQLite schema...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r") as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()

    print("✓ Schema initialized successfully!")
