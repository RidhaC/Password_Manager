# database/db_crypto.py

import os
import shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_FILE   = os.path.join(os.path.dirname(__file__), '..', 'electron-app', '.secret_key')
DB_ENC     = os.path.join(os.path.dirname(__file__), '..', 'electron-app', 'vault_accounts.db.enc')
DB_PLAIN   = os.path.join(os.path.dirname(__file__), '..', 'electron-app', 'vault_accounts.db')

def _get_key() -> bytes:
    with open(KEY_FILE, 'rb') as f:
        raw = f.read()
    # derive a 32-byte key from the secret key
    import hashlib
    return hashlib.sha256(raw).digest()

def encrypt_db():
    if not os.path.exists(DB_PLAIN):
        return
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    with open(DB_PLAIN, 'rb') as f:
        plaintext = f.read()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    with open(DB_ENC, 'wb') as f:
        f.write(nonce + ciphertext)
    os.remove(DB_PLAIN)

def decrypt_db():
    if not os.path.exists(DB_ENC):
        return  # first run, no encrypted db yet
    key = _get_key()
    aesgcm = AESGCM(key)
    with open(DB_ENC, 'rb') as f:
        data = f.read()
    nonce, ciphertext = data[:12], data[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    with open(DB_PLAIN, 'wb') as f:
        f.write(plaintext)
    os.remove(DB_ENC)

def is_encrypted():
    return os.path.exists(DB_ENC) and not os.path.exists(DB_PLAIN)