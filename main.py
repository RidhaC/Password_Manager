# main.py

import threading
import atexit
import os
import sys
from app import app
from database.users import database_create
from database.db_crypto import decrypt_db, encrypt_db

def run_flask():
    app.run(debug=False, port=5000, use_reloader=False)

def ensure_schema():
    """Make sure all columns exist before running."""
    from database.connection import get_connection
    conn = get_connection()
    migrations = [
        "ALTER TABLE vault ADD COLUMN category TEXT DEFAULT 'other'",
        "ALTER TABLE vault ADD COLUMN last_used TEXT DEFAULT NULL",
        """CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vault_id INTEGER NOT NULL,
            enc_password TEXT NOT NULL,
            changed_at TEXT NOT NULL,
            FOREIGN KEY(vault_id) REFERENCES vault(id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS custom_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            color TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES accounts(id) ON DELETE CASCADE
        )""",
        "ALTER TABLE accounts ADD COLUMN first_name TEXT DEFAULT ''",
        "ALTER TABLE accounts ADD COLUMN last_name TEXT DEFAULT ''",
        "ALTER TABLE accounts ADD COLUMN email TEXT DEFAULT ''",
        "ALTER TABLE accounts ADD COLUMN theme TEXT DEFAULT 'dark'",
    ]
    for m in migrations:
        try:
            conn.execute(m)
            conn.commit()
        except Exception:
            pass
    conn.close()

def shutdown():
    print("Encrypting database...")
    encrypt_db()
    print("Done.")

if __name__ == "__main__":
    decrypt_db()
    database_create()
    ensure_schema()
    atexit.register(shutdown)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    flask_thread.join()
