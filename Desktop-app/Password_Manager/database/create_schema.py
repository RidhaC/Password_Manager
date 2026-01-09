import sys, os
# Add the parent directory (Password_Manager) to the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import database_path
import sqlite3

def create_database():
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    # --- accounts table ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt BLOB NOT NULL,
        enc_salt BLOB NOT NULL
    )
    """)

    # --- vault table ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vault (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        account_username TEXT,
        enc_password TEXT NOT NULL,
        url TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES accounts(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()
    print("New database created successfully at:", database_path)

if __name__ == "__main__":
    create_database()
