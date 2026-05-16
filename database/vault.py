# database/vault.py

import hashlib
from datetime import datetime
from .connection import get_connection
from .encryption import _derive_aes_key, _aes_encrypt_gcm, _aes_decrypt_gcm


def _get_user_and_key(username: str, master_password: str):
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


def save_secret(username, master_pw, label, account_username, secret_password, url, notes, category="other"):
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return False
    cur = conn.cursor()
    enc_label = _aes_encrypt_gcm(label, key)
    enc_user  = _aes_encrypt_gcm(account_username, key)
    enc_pass  = _aes_encrypt_gcm(secret_password, key)
    enc_notes = _aes_encrypt_gcm(notes, key) if notes else None
    now = datetime.now().isoformat()
    cur.execute(
        """
        INSERT INTO vault (user_id, label, account_username, enc_password, url, notes, last_updated, last_used, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, enc_label, enc_user, enc_pass, url, enc_notes, now, now, category),
    )
    conn.commit()
    conn.close()
    return True


def get_secrets(username, master_pw, sort_by='last_used'):
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return []
    cur = conn.cursor()
    order = {
        'last_used': 'COALESCE(last_used, last_updated, "1970") DESC',
        'last_updated': 'COALESCE(last_updated, "1970") DESC',
        'newest': 'id DESC',
        'oldest': 'id ASC',
    }.get(sort_by, 'COALESCE(last_used, last_updated, "1970") DESC')

    cur.execute(
        f"""
        SELECT id, label, account_username, enc_password, url, notes, last_updated, category, last_used
        FROM vault WHERE user_id = ?
        ORDER BY {order}
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    secrets = []
    for vid, enc_label, enc_user, enc_pass, url, enc_notes, last_updated, category, last_used in rows:
        try:
            label     = _aes_decrypt_gcm(enc_label, key)
            acc_user  = _aes_decrypt_gcm(enc_user, key)
            password  = _aes_decrypt_gcm(enc_pass, key)
            notes_dec = _aes_decrypt_gcm(enc_notes, key) if enc_notes else ""
        except Exception:
            label = acc_user = password = notes_dec = "(decrypt error)"
        secrets.append({
            "id":               vid,
            "label":            label,
            "account_username": acc_user,
            "password":         password,
            "url":              url or "",
            "notes":            notes_dec,
            "last_updated":     last_updated,
            "last_used":        last_used,
            "category":         category or "other",
        })

    if sort_by == 'alpha':
        secrets.sort(key=lambda s: s['label'].lower())

    return secrets


def delete_secret(username, master_password, label):
    try:
        conn, user_id, key = _get_user_and_key(username, master_password)
        if not user_id:
            return False

        cur = conn.cursor()
        cur.execute("SELECT id, label FROM vault WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()

        for sid, enc_label in rows:
            try:
                if _aes_decrypt_gcm(enc_label, key) == label:
                    cur.execute("DELETE FROM vault WHERE id = ?", (sid,))
                    conn.commit()
                    conn.close()
                    return True
            except Exception:
                continue

        conn.close()
        return False
    except Exception as e:
        print("Delete error:", e)
        return False


def update_secret(username, master_pw, old_label, new_label, new_user, new_pass, new_url, new_notes, category="other"):
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return False
    cur = conn.cursor()
    cur.execute("SELECT id, label, enc_password FROM vault WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    target_id = None
    old_enc_pass = None
    for sid, enc_label, enc_pass in rows:
        try:
            if _aes_decrypt_gcm(enc_label, key) == old_label:
                target_id = sid
                old_enc_pass = enc_pass
                break
        except Exception:
            continue
    if not target_id:
        conn.close()
        return False

    # Save password history before updating
    if old_enc_pass:
        cur.execute(
            "INSERT INTO password_history (vault_id, enc_password, changed_at) VALUES (?, ?, ?)",
            (target_id, old_enc_pass, datetime.now().isoformat())
        )
        # Keep only last 10 history entries per vault item
        cur.execute(
            """DELETE FROM password_history WHERE vault_id = ? AND id NOT IN (
                SELECT id FROM password_history WHERE vault_id = ? ORDER BY changed_at DESC LIMIT 10
            )""",
            (target_id, target_id)
        )

    enc_label = _aes_encrypt_gcm(new_label, key)
    enc_user  = _aes_encrypt_gcm(new_user, key)
    enc_pass  = _aes_encrypt_gcm(new_pass, key)
    enc_notes = _aes_encrypt_gcm(new_notes, key) if new_notes else None
    now = datetime.now().isoformat()
    cur.execute(
        """
        UPDATE vault
        SET label=?, account_username=?, enc_password=?, url=?, notes=?, last_updated=?, last_used=?, category=?
        WHERE id=?
        """,
        (enc_label, enc_user, enc_pass, new_url, enc_notes, now, now, category, target_id),
    )
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok

def mark_secret_used(username, master_pw, label):
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return False
    cur = conn.cursor()
    cur.execute("SELECT id, label FROM vault WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    for sid, enc_label in rows:
        try:
            if _aes_decrypt_gcm(enc_label, key) == label:
                cur.execute("UPDATE vault SET last_used=? WHERE id=?", (datetime.now().isoformat(), sid))
                conn.commit()
                conn.close()
                return True
        except Exception:
            continue
    conn.close()
    return False


def get_password_history(username, master_pw, label):
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return []
    cur = conn.cursor()
    cur.execute("SELECT id, label FROM vault WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    vault_id = None
    for sid, enc_label in rows:
        try:
            if _aes_decrypt_gcm(enc_label, key) == label:
                vault_id = sid
                break
        except Exception:
            continue
    if not vault_id:
        conn.close()
        return []
    cur.execute(
        "SELECT enc_password, changed_at FROM password_history WHERE vault_id=? ORDER BY changed_at DESC",
        (vault_id,)
    )
    history = []
    for enc_pass, changed_at in cur.fetchall():
        try:
            pw = _aes_decrypt_gcm(enc_pass, key)
            history.append({"password": pw, "changed_at": changed_at})
        except Exception:
            continue
    conn.close()
    return history

def get_all_credentials(username, master_pw):
    conn, user_id, key = _get_user_and_key(username, master_pw)
    if not user_id:
        return []

    cur = conn.cursor()
    cur.execute(
        """
        SELECT label, account_username, enc_password, url, notes, last_updated, category
        FROM vault WHERE user_id = ?
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()

    creds = []
    for r in rows:
        try:
            label    = _aes_decrypt_gcm(r[0], key)
            acc_user = _aes_decrypt_gcm(r[1], key)
            password = _aes_decrypt_gcm(r[2], key)
        except Exception:
            continue
        creds.append({
            "label":            label,
            "account_username": acc_user,
            "password":         password,
            "url":              r[3],
            "notes":            r[4],
            "last_updated":     r[5],
            "category":         r[6] or "other",
        })
    return creds
