# database/session.py

import json
import os
import time
import hashlib
import hmac

SESSION_FILE = os.path.join(os.path.dirname(__file__), '..', 'electron-app', '.sessions.json')
THIRTY_DAYS = 30 * 24 * 60 * 60

def _get_hmac_key():
    key_file = os.path.join(os.path.dirname(__file__), '..', 'electron-app', '.secret_key')
    with open(key_file, 'rb') as f:
        return f.read()

def _sign(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True)
    key = _get_hmac_key()
    import hmac as _hmac
    return _hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()

def _load():
    try:
        with open(SESSION_FILE, 'r') as f:
            stored = json.load(f)
        sig = stored.pop('__sig__', None)
        data = stored
        expected = _sign(data)
        if not hmac.compare_digest(sig or '', expected):
            return {}
        return data
    except Exception:
        return {}

def _save(data):
    try:
        sig = _sign(data)
        with open(SESSION_FILE, 'w') as f:
            json.dump({**data, '__sig__': sig}, f)
    except Exception:
        pass

def _key(username):
    return hashlib.sha256(username.encode()).hexdigest()

def mark_2fa_verified(username):
    data = _load()
    data[_key(username)] = time.time()
    _save(data)

def is_2fa_recent(username):
    data = _load()
    last = data.get(_key(username), 0)
    return (time.time() - last) < THIRTY_DAYS

def clear_2fa_session(username):
    data = _load()
    data.pop(_key(username), None)
    _save(data)
    