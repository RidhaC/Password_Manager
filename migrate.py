import sqlite3

conn = sqlite3.connect('electron-app/vault_accounts.db')
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

cols = [c[1] for c in conn.execute("PRAGMA table_info(vault)").fetchall()]
print("Vault columns:", cols)

if 'category' not in cols:
    conn.execute("ALTER TABLE vault ADD COLUMN category TEXT DEFAULT 'other'")
    conn.commit()
    print("Done - category column added")
else:
    print("Column already exists")

conn.close()

conn2 = sqlite3.connect('electron-app/vault_accounts.db')
migrations = [
    "ALTER TABLE accounts ADD COLUMN first_name TEXT DEFAULT ''",
    "ALTER TABLE accounts ADD COLUMN last_name TEXT DEFAULT ''",
    "ALTER TABLE accounts ADD COLUMN email TEXT DEFAULT ''",
    "ALTER TABLE accounts ADD COLUMN theme TEXT DEFAULT 'dark'",
    """CREATE TABLE IF NOT EXISTS custom_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        icon TEXT NOT NULL,
        color TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES accounts(id) ON DELETE CASCADE
    )""",
]
for m in migrations:
    try:
        conn2.execute(m)
        print('OK:', m[:50])
    except Exception as e:
        print('Skip:', e)
conn2.commit()

migrations2 = [
    "ALTER TABLE vault ADD COLUMN last_used TEXT DEFAULT NULL",
    """CREATE TABLE IF NOT EXISTS password_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vault_id INTEGER NOT NULL,
        enc_password TEXT NOT NULL,
        changed_at TEXT NOT NULL,
        FOREIGN KEY(vault_id) REFERENCES vault(id) ON DELETE CASCADE
    )""",
]
for m in migrations2:
    try:
        conn2.execute(m)
        print('OK:', m[:50])
    except Exception as e:
        print('Skip:', e)
conn2.commit()

conn2.close()
