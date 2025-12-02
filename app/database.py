"""
Database Connection Manager
SQLite version for Vercel & local development
"""
import sqlite3
from flask import g
import os

# Path for SQLite DB
# On Vercel, only /tmp is writeable
DB_PATH = os.path.join("/tmp", "database.db")

def init_db(app):
    """
    Initialize SQLite database.
    Creates file automatically if missing.
    Runs schema if provided.
    """
    # Ensure DB file exists
    if not os.path.exists(DB_PATH):
        print("Creating new SQLite DB at:", DB_PATH)
        open(DB_PATH, 'a').close()
    else:
        print("Using existing SQLite DB at:", DB_PATH)

def get_db():
    """
    Returns a SQLite connection for the current request.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # returns dict-like rows
    return g.db

def close_db(e=None):
    """
    Closes DB connection after request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False, commit=False):
    """
    Executes SQL query with parameters.
    """
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(query, args)

        if commit:
            db.commit()
            return cursor.lastrowid

        rows = cursor.fetchall()
        rows = [dict(row) for row in rows]

        return (rows[0] if rows else None) if one else rows

    except Exception as e:
        db.rollback()
        print("SQLite error:", e)
        raise

    finally:
        cursor.close()
