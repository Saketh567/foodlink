"""
Database Connection Manager
MySQL implementation for local and hosted environments
"""
import pymysql
from flask import current_app, g


def init_db(app):
    """
    Validate MySQL connectivity at startup.
    """
    try:
        conn = pymysql.connect(
            host=app.config["MYSQL_HOST"],
            port=app.config["MYSQL_PORT"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DATABASE"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        conn.close()
        print(
            f"Connected to MySQL at {app.config['MYSQL_HOST']}:{app.config['MYSQL_PORT']} "
            f"(DB: {app.config['MYSQL_DATABASE']})"
        )
    except Exception as exc:
        print("Failed to connect to MySQL:", exc)
        raise


def get_db():
    """
    Returns a MySQL connection for the current request context.
    """
    if "db" not in g:
        g.db = pymysql.connect(
            host=current_app.config["MYSQL_HOST"],
            port=current_app.config["MYSQL_PORT"],
            user=current_app.config["MYSQL_USER"],
            password=current_app.config["MYSQL_PASSWORD"],
            database=current_app.config["MYSQL_DATABASE"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
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
    Executes SQL query with parameters against MySQL.
    """
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(query, args)

        if commit:
            db.commit()
            return cursor.lastrowid

        rows = cursor.fetchall()
        return (rows[0] if rows else None) if one else rows

    except Exception as exc:
        db.rollback()
        print("MySQL error:", exc)
        raise

    finally:
        cursor.close()
