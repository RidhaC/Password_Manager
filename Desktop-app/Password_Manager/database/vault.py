"""
Encrypted password storage with AES-GCM field encryption.

Includes timestamps for last updates to support the alerts feature.
"""

import hashlib
from datetime import datetime
from .connection import get_connection
from .encryption import _derive_aes_key, _aes_encrypt_gcm, _aes_decrypt_gcm
import sqlite3


def _get_user_and_key(username: str, master_password: str):
    """Return (connection, user_id, AES key) derived from user's master password."""
    u_hash = hashlib.sha256(username.encode("utf-8")).hexdigest()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, enc_salt FROM accounts WHERE username_hash = ?", (u_hash,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return None, None, None

    user_id, enc_salt = row
    key = _derive_aes_key(master_password, enc_salt)
    return conn, user_id, key


def save_secret(username, master_pw, label, account_username, secret_password, url, notes):
    """Encrypt and save a new password record."""
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return False

    cur = conn.cursor()
    enc_label = _aes_encrypt_gcm(label, key)
    enc_user = _aes_encrypt_gcm(account_username, key)
    enc_pass = _aes_encrypt_gcm(secret_password, key)
    enc_notes = _aes_encrypt_gcm(notes, key) if notes else None
    last_updated = datetime.now().isoformat()

    cur.execute(
        """
        INSERT INTO vault (user_id, label, account_username, enc_password, url, notes, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, enc_label, enc_user, enc_pass, url, enc_notes, last_updated),
    )

    conn.commit()
    conn.close()
    return True

# Retrieve and decrypt all stored secrets for a user
def get_secrets(username, master_pw):
    """Retrieve and decrypt all stored secrets for a user."""
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return []

    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, label, account_username, enc_password, url, notes
        FROM vault
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )

    rows = cur.fetchall()
    conn.close()

    secrets = []
    for vid, enc_label, enc_user, enc_pass, url, enc_notes in rows:
        try:
            label = _aes_decrypt_gcm(enc_label, key)
            acc_user = _aes_decrypt_gcm(enc_user, key)
            password = _aes_decrypt_gcm(enc_pass, key)
            notes = _aes_decrypt_gcm(enc_notes, key) if enc_notes else ""
        except Exception:
            label = acc_user = password = notes = "(decrypt error)"
        secrets.append(
            {
                "id": vid,
                "label": label,
                "account_username": acc_user,
                "password": password,
                "url": url or "",
                "notes": notes,
            }
        )

    return secrets

# Delete a stored secret by label
def delete_secret(username, master_password, label):
    """Deletes a stored secret by decrypting each label and matching it."""
    try:
        # Reuse AES key and user_id from helper
        conn, user_id, key = _get_user_and_key(username, master_password)
        if not user_id:
            return False

        cur = conn.cursor()
        cur.execute("SELECT id, label FROM vault WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()

        deleted = False
        for sid, enc_label in rows:
            try:
                dec_label = _aes_decrypt_gcm(enc_label, key)
                if dec_label == label:
                    cur.execute("DELETE FROM vault WHERE id = ?", (sid,))
                    conn.commit()
                    deleted = True
                    break
            except Exception:
                continue

        conn.close()
        return deleted

    except Exception as e:
        print("Delete error:", e)
        return False

# Update an existing stored secret
def update_secret(username, master_pw, old_label, new_user, new_pass, new_url, new_notes):
    """Update a stored record and refresh its last_updated timestamp."""
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return False

    cur = conn.cursor()
    cur.execute("SELECT id, label FROM vault WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()

    target_id = None
    for sid, enc_label in rows:
        try:
            dec_label = _aes_decrypt_gcm(enc_label, key)
            if dec_label == old_label:
                target_id = sid
                break
        except Exception:
            continue

    if not target_id:
        conn.close()
        return False

    enc_user = _aes_encrypt_gcm(new_user, key)
    enc_pass = _aes_encrypt_gcm(new_pass, key)
    enc_notes = _aes_encrypt_gcm(new_notes, key) if new_notes else None
    last_updated = datetime.now().isoformat()

    cur.execute(
        """
        UPDATE vault
        SET account_username = ?, enc_password = ?, url = ?, notes = ?, last_updated = ?
        WHERE id = ?
        """,
        (enc_user, enc_pass, new_url, enc_notes, last_updated, target_id),
    )

    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok

# Retrieve all stored credentials (decrypted) for a given user
def get_all_credentials(username, master_pw):
    """Return all stored credentials (decrypted) for a given user."""
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return []

    cur = conn.cursor()
    cur.execute(
        """
        SELECT label, account_username, enc_password, url, notes, last_updated
        FROM vault
        WHERE user_id = ?
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()

    creds = []
    for r in rows:
        try:
            label = _aes_decrypt_gcm(r[0], key)
            acc_user = _aes_decrypt_gcm(r[1], key)
            password = _aes_decrypt_gcm(r[2], key)
            last_updated = r[5]
        except Exception:
            continue

        creds.append(
            {
                "label": label,
                "account_username": acc_user,
                "password": password,
                "url": r[3],
                "notes": r[4],
                "last_updated": last_updated,
            }
        )
    return creds
