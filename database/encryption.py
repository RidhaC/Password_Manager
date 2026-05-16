# database/encryption.py


import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _random_salt(length: int = 16) -> bytes:
    return os.urandom(length)

def _hash_pw_with_salt(password: str, salt: bytes) -> str:
    
    return hashlib.sha256(salt + password.encode("utf-8")).hexdigest()

def _derive_aes_key(master_password: str, enc_salt: bytes) -> bytes:
    
    return hashlib.pbkdf2_hmac('sha256', master_password.encode('utf-8'), enc_salt, 200_000, dklen=32)

def _aes_encrypt_gcm(plaintext: str, key: bytes) -> str: 
    aesgcm = AESGCM(key)  
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    token = nonce + ct 
    return base64.urlsafe_b64encode(token).decode('ascii')

def _aes_decrypt_gcm(token: str, key: bytes) -> str:
    raw = base64.urlsafe_b64decode(token)  
    nonce, ct = raw[:12], raw[12:]  
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ct, None)  
    return pt.decode('utf-8')
