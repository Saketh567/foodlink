"""
Utility to initialize the MySQL schema from migrations/schema.sql.
Run manually if you need to reseed the database.
"""
import os

import pymysql
from pymysql.constants import CLIENT

from app.config import Config

SCHEMA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "migrations", "schema.sql")
)


def initialize_schema():
    """
    Execute migrations/schema.sql against the configured MySQL database.
    """
    cfg = Config()
    print("Initializing MySQL schema...")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
        sql_script = schema_file.read()

    connection = pymysql.connect(
        host=cfg.MYSQL_HOST,
        port=cfg.MYSQL_PORT,
        user=cfg.MYSQL_USER,
        password=cfg.MYSQL_PASSWORD,
        database=cfg.MYSQL_DATABASE,
        charset="utf8mb4",
        client_flag=CLIENT.MULTI_STATEMENTS,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_script)
            while cursor.nextset():
                pass
        connection.commit()
        print("Schema initialized successfully.")
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_schema()
