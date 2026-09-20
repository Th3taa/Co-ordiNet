"""Recreate the local Co-ordinet database from the checked-in SQL scripts."""
import argparse
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


script_directory = Path(__file__).resolve().parent
project_directory = script_directory.parent
load_dotenv(project_directory / ".env")


def database_config() -> dict:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
    }


def run_sql_file(cursor, filename: str, database_name: str) -> None:
    sql_text = (script_directory / filename).read_text(encoding="ascii")
    sql_text = sql_text.replace("co_ordinet", database_name)
    for statement in sql_text.split(";"):
        query = statement.strip()
        if query:
            cursor.execute(query)


def reset_database() -> None:
    database_name = os.getenv("MYSQL_DATABASE", "co_ordinet")
    if not database_name.replace("_", "").isalnum():
        raise ValueError("MYSQL_DATABASE may contain only letters, numbers, and underscores.")
    connection = mysql.connector.connect(**database_config())
    cursor = connection.cursor()
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
        run_sql_file(cursor, "01_create_database.sql", database_name)
        run_sql_file(cursor, "02_create_tables.sql", database_name)
        run_sql_file(cursor, "03_seed_students.sql", database_name)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Drop and rebuild the configured Co-ordinet database.")
    parser.add_argument("--confirm-drop", action="store_true", help="Required because this permanently deletes the current database.")
    args = parser.parse_args()
    if not args.confirm_drop:
        parser.error("Refusing to drop the database without --confirm-drop.")
    reset_database()
    print("Co-ordinet database recreated and sample students seeded.")


if __name__ == "__main__":
    main()
