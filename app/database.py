import mysql.connector
from flask import g
from mysql.connector import pooling
from .config import Config

pool = None

def init_db(app):
    global pool
    pool = pooling.MySQLConnectionPool(
        pool_name="foodlink_pool",
        pool_size=5,
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        database=Config.DB_NAME,
    )

    @app.teardown_appcontext
    def close_connection(exception):
        conn = g.pop("db_conn", None)
        if conn:
            conn.close()


def get_db():
    if "db_conn" not in g:
        g.db_conn = pool.get_connection()
    return g.db_conn


def query_db(query, args=(), one=False, commit=False):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, args)

    if commit:
        conn.commit()
        cursor.close()
        return None

    result = cursor.fetchone() if one else cursor.fetchall()
    cursor.close()
    return result
