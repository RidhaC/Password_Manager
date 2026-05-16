# database/users.py

import hashlib
import hmac
import pyotp
import base64
import os
from .connection import get_connection
from .encryption import _random_salt, _hash_pw_with_salt
from .LO_BC import ensure_security_tables

def database_create():
    connect = get_connection()
    cur = connect.cursor()

    # --- Accounts table ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            username_hash TEXT NOT NULL,
            password_salt BLOB NOT NULL,
            password_hash TEXT NOT NULL,
            enc_salt BLOB NOT NULL,
            totp_secretkey TEXT,
            totp_enabled INTEGER DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            label TEXT NOT NULL,
            account_username TEXT NOT NULL,
            enc_password TEXT NOT NULL,
            url TEXT,
            notes TEXT,
            last_updated TEXT,
            FOREIGN KEY(user_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
        """
    )

    connect.commit()
    ensure_security_tables()
    connect.close()


def datebase_create():
    return database_create()
    

def create_user(username: str, password: str) -> bool:
    salt = _random_salt()
    pw_hash = _hash_pw_with_salt(password, salt)
    u_hash = hashlib.sha256(username.encode("utf-8")).hexdigest()
    enc_salt = _random_salt()

    try:
        connect = get_connection()
        cur = connect.cursor()
        secretkey = base64.b32encode(os.urandom(10)).decode("utf-8")
        cur.execute(
            "INSERT INTO accounts (username, username_hash, password_salt, password_hash, enc_salt, totp_secretkey, totp_enabled) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, u_hash, salt, pw_hash, enc_salt, secretkey, 0),
        )
        connect.commit()
        return True

    except Exception:
        return False

    finally:
        try:
            connect.close()
        except Exception:
            pass


def user_verification(username: str, password: str) -> bool:
    connect = get_connection()
    cur = connect.cursor()
    cur.execute("SELECT password_salt, password_hash FROM accounts WHERE username = ?", (username,))
    row = cur.fetchone()
    if row is None:
        cur.execute("SELECT password_salt, password_hash FROM accounts WHERE email = ?", (username,))
        row = cur.fetchone()
    connect.close()
    if row is None:
        return False
    stored_salt, stored_hash = row[0], row[1]
    computed = _hash_pw_with_salt(password, stored_salt)
    try:
        return hmac.compare_digest(computed, stored_hash)
    except Exception:
        return False


def get_user_totp_secretkey(username):
    connect = get_connection()
    cur = connect.cursor()
    cur.execute("SELECT totp_secretkey FROM accounts WHERE username = ?", (username,))
    row = cur.fetchone()
    connect.close()
    return row[0] if row else None

def get_user_profile(username: str) -> dict:
    connect = get_connection()
    cur = connect.cursor()
    cur.execute("SELECT first_name, last_name, email, theme FROM accounts WHERE username = ?", (username,))
    row = cur.fetchone()
    connect.close()
    if not row:
        return {}
    return {"first_name": row[0] or "", "last_name": row[1] or "", "email": row[2] or "", "theme": row[3] or "dark"}

def update_user_profile(username: str, first_name: str, last_name: str, email: str) -> bool:
    try:
        connect = get_connection()
        cur = connect.cursor()
        cur.execute("UPDATE accounts SET first_name=?, last_name=?, email=? WHERE username=?", (first_name, last_name, email, username))
        connect.commit()
        connect.close()
        return True
    except Exception:
        return False

def update_user_password(username: str, old_password: str, new_password: str) -> bool:
    if not user_verification(username, old_password):
        return False
    try:
        salt = _random_salt()
        pw_hash = _hash_pw_with_salt(new_password, salt)
        connect = get_connection()
        cur = connect.cursor()
        cur.execute("UPDATE accounts SET password_salt=?, password_hash=? WHERE username=?", (salt, pw_hash, username))
        connect.commit()
        connect.close()
        return True
    except Exception:
        return False

def update_user_theme(username: str, theme: str) -> bool:
    try:
        connect = get_connection()
        cur = connect.cursor()
        cur.execute("UPDATE accounts SET theme=? WHERE username=?", (theme, username))
        connect.commit()
        connect.close()
        return True
    except Exception:
        return False

def get_custom_categories(username: str) -> list:
    connect = get_connection()
    cur = connect.cursor()
    cur.execute("SELECT id FROM accounts WHERE username=?", (username,))
    row = cur.fetchone()
    if not row:
        connect.close()
        return []
    user_id = row[0]
    cur.execute("SELECT id, name, icon, color FROM custom_categories WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    connect.close()
    return [{"id": r[0], "name": r[1], "icon": r[2], "color": r[3]} for r in rows]

def add_custom_category(username: str, name: str, icon: str, color: str) -> bool:
    try:
        connect = get_connection()
        cur = connect.cursor()
        cur.execute("SELECT id FROM accounts WHERE username=?", (username,))
        row = cur.fetchone()
        if not row:
            connect.close()
            return False
        cur.execute("INSERT INTO custom_categories (user_id, name, icon, color) VALUES (?,?,?,?)", (row[0], name, icon, color))
        connect.commit()
        connect.close()
        return True
    except Exception:
        return False

def delete_custom_category(username: str, category_id: int) -> bool:
    try:
        connect = get_connection()
        cur = connect.cursor()
        cur.execute("SELECT id FROM accounts WHERE username=?", (username,))
        row = cur.fetchone()
        if not row:
            connect.close()
            return False
        cur.execute("DELETE FROM custom_categories WHERE id=? AND user_id=?", (category_id, row[0]))
        connect.commit()
        connect.close()
        return True
    except Exception:
        return False

def set_2fa_enabled(username, enabled: bool):
    connect = get_connection()
    cur = connect.cursor()
    cur.execute(
        "UPDATE accounts SET totp_enabled = ? WHERE username = ?",
        (1 if enabled else 0, username),
    )
    connect.commit()
    connect.close()
