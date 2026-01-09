# database/security.py
"""
Security helpers:
- Login attempt lockout (throttles brute-force)
- TOTP backup codes (hashed, one-time use)
"""

import time
import hashlib
from typing import List, Tuple
from .connection import get_connection

# --- internal helpers ---

def _username_hash(username: str) -> str:
    return hashlib.sha256(username.encode("utf-8")).hexdigest()

def _get_user_id(username: str):
    uhash = _username_hash(username)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM accounts WHERE username_hash = ?", (uhash,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

# --- schema ---

def ensure_security_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lockouts (
            user_id INTEGER PRIMARY KEY,
            attempts INTEGER NOT NULL DEFAULT 0,
            locked_until REAL NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS backup_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code_hash TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

# --- lockout API ---

def is_user_locked(username: str) -> Tuple[bool, int]:
    """Return (locked?, seconds_remaining)."""
    uid = _get_user_id(username)
    if not uid:
        return False, 0
    now = time.time()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT locked_until FROM lockouts WHERE user_id = ?", (uid,))
    row = cur.fetchone()
    conn.close()
    until = float(row[0]) if row else 0.0
    if until > now:
        return True, int(until - now)
    return False, 0

def register_failed_attempt(username: str, max_attempts: int, lockout_seconds: int) -> int:
    """Increment attempts; lock if >= max_attempts. Return attempts remaining before lock."""
    uid = _get_user_id(username)
    if not uid:
        return 0
    now = time.time()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT attempts, locked_until FROM lockouts WHERE user_id = ?", (uid,))
    row = cur.fetchone()
    attempts, locked_until = (row if row else (0, 0.0))
    if locked_until and locked_until <= now:
        attempts, locked_until = 0, 0.0
    attempts += 1
    if attempts >= max_attempts:
        locked_until = now + lockout_seconds
    if row:
        cur.execute("UPDATE lockouts SET attempts=?, locked_until=? WHERE user_id=?",
                    (attempts, locked_until, uid))
    else:
        cur.execute("INSERT INTO lockouts (user_id, attempts, locked_until) VALUES (?, ?, ?)",
                    (uid, attempts, locked_until))
    conn.commit(); conn.close()
    return max(0, max_attempts - attempts)

def reset_attempts(username: str):
    uid = _get_user_id(username)
    if not uid:
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO lockouts (user_id, attempts, locked_until) VALUES (?, 0, 0)
                   ON CONFLICT(user_id) DO UPDATE SET attempts=0, locked_until=0""", (uid,))
    conn.commit(); conn.close()

# --- backup codes API ---

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def generate_backup_codes(n: int = 10, length: int = 10) -> List[str]:
    import secrets
    alphabet = "0123456789"
    return ["".join(secrets.choice(alphabet) for _ in range(length)) for __ in range(n)]

def store_backup_codes(username: str, plain_codes: List[str]) -> None:
    uid = _get_user_id(username)
    if not uid:
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM backup_codes WHERE user_id = ?", (uid,))
    cur.executemany("INSERT INTO backup_codes (user_id, code_hash, used) VALUES (?, ?, 0)",
                    [(uid, _hash_code(c)) for c in plain_codes])
    conn.commit(); conn.close()

def remaining_backup_count(username: str) -> int:
    uid = _get_user_id(username)
    if not uid:
        return 0
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM backup_codes WHERE user_id=? AND used=0", (uid,))
    n = cur.fetchone()[0]
    conn.close()
    return int(n)

def consume_backup_code(username: str, code: str) -> bool:
    uid = _get_user_id(username)
    if not uid:
        return False
    h = _hash_code(code.strip())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT id FROM backup_codes
                   WHERE user_id=? AND code_hash=? AND used=0""", (uid, h))
    row = cur.fetchone()
    if not row:
        conn.close(); return False
    cur.execute("UPDATE backup_codes SET used=1 WHERE id=?", (row[0],))
    conn.commit(); conn.close()
    return True
