
import sqlite3
import pymysql
import os
from pathlib import Path

# MySQL Configuration (Default values, change if needed)
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "hkgai@123")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "sora_watermark_cleaner")

# SQLite Configuration
SQLITE_DB_PATH = Path("data/db.sqlite3")

def get_mysql_connection():
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def migrate_data():
    if not SQLITE_DB_PATH.exists():
        print(f"SQLite database not found at {SQLITE_DB_PATH}. Please runs 'python init_database.py' first to create the schema.")
        return

    # Connect to MySQL
    mysql_conn = get_mysql_connection()
    if not mysql_conn:
        return

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    try:
        with mysql_conn.cursor() as cursor:
            # 1. Migrate Users
            print("Migrating users...")
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            for user in users:
                # Prepare insert statement. Note: Column names must match SQLite schema
                # We use INSERT OR IGNORE to avoid duplicates if run multiple times
                columns = ', '.join(user.keys())
                placeholders = ', '.join(['?'] * len(user))
                values = list(user.values())
                
                query = f"INSERT OR IGNORE INTO users ({columns}) VALUES ({placeholders})"
                sqlite_cursor.execute(query, values)
            
            print(f"Migrated {len(users)} users.")

            # 2. Migrate Tasks
            print("Migrating tasks...")
            cursor.execute("SELECT * FROM tasks")
            tasks = cursor.fetchall()
            
            for task in tasks:
                columns = ', '.join(task.keys())
                placeholders = ', '.join(['?'] * len(task))
                values = list(task.values())
                
                query = f"INSERT OR IGNORE INTO tasks ({columns}) VALUES ({placeholders})"
                sqlite_cursor.execute(query, values)
            
            print(f"Migrated {len(tasks)} tasks.")

        sqlite_conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        sqlite_conn.rollback()
    finally:
        mysql_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    print("Starting migration from MySQL to SQLite...")
    print(f"MySQL Source: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    print(f"SQLite Target: {SQLITE_DB_PATH}")
    migrate_data()
