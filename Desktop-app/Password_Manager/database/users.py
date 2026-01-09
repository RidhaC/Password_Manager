"""
This file contains functions to manage the SQLite database for user accounts.

It handles creating new users, verifying credentials using salted SHA256 hashes,
and includes AES key derivation salts for encryption. It also defines the full
schema for the 'accounts' and 'vault' tables (with last_updated for alerts).
"""

import hashlib
import hmac
import pyotp
import base64
import os
from .connection import get_connection
from .encryption import _random_salt, _hash_pw_with_salt
from .LO_BC import ensure_security_tables

def database_create():
    """Creates database tables if they do not already exist."""
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

    # --- Vault table (includes last_updated for alerts) ---
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
    """Wrapper to maintain compatibility with earlier imports."""
    return database_create()
    

def create_user(username: str, password: str) -> bool:
    """Creates a new user in the database. Returns True if successful."""
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
    """Verifies login credentials and returns True if valid."""
    connect = get_connection()
    cur = connect.cursor()
    cur.execute("SELECT password_salt, password_hash FROM accounts WHERE username = ?", (username,))
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
    """Retrieve the TOTP secret key for a given username."""
    connect = get_connection()
    cur = connect.cursor()
    cur.execute("SELECT totp_secretkey FROM accounts WHERE username = ?", (username,))
    row = cur.fetchone()
    connect.close()
    return row[0] if row else None


def set_2fa_enabled(username, enabled: bool):
    """Enable or disable 2FA for a user."""
    connect = get_connection()
    cur = connect.cursor()
    cur.execute(
        "UPDATE accounts SET totp_enabled = ? WHERE username = ?",
        (1 if enabled else 0, username),
    )
    connect.commit()
    connect.close()
