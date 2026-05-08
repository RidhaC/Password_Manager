# database/encryption.py
"""
This module contains AES-256 helper functions to encrypt and decrypt sensitive values
and hashing/key-derivation helpers, extracted from database.py to keep the code organized.
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _random_salt(length: int = 16) -> bytes:
    # os.urandom(length) generates a cryptographically secure random salt
    return os.urandom(length)

def _hash_pw_with_salt(password: str, salt: bytes) -> str:
    # this combines the salt and password bytes before hashing to protect against rainbow tables
    # .hexdigest() returns the final salted password hash as a hexadecimal string
    return hashlib.sha256(salt + password.encode("utf-8")).hexdigest()

def _derive_aes_key(master_password: str, enc_salt: bytes) -> bytes:
    # hashlib.pbkdf2_hmac() derives a strong key from the user's password using HMAC-SHA256 with many iterations
    # dklen=32 requests a 256-bit derived key suitable for AES-256
    return hashlib.pbkdf2_hmac('sha256', master_password.encode('utf-8'), enc_salt, 200_000, dklen=32)

def _aes_encrypt_gcm(plaintext: str, key: bytes) -> str:  # encrypts a plaintext using AES-256-GCM and returns a URL-safe base64 token
    aesgcm = AESGCM(key)  # AESGCM() will create an AESGCM object with the provided key
    nonce = os.urandom(12)  # os.urandom(12) generates a random 12-byte nonce
    ct = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)  # encrypts the plaintext with the nonce and key
    token = nonce + ct  # pack nonce and ciphertext together
    return base64.urlsafe_b64encode(token).decode('ascii')  # encode as URL-safe base64 string for storage

def _aes_decrypt_gcm(token: str, key: bytes) -> str:
    # decrypts a URL-safe base64 token produced by _aes_encrypt_gcm and returns the original plaintext
    raw = base64.urlsafe_b64decode(token)  # decode token to bytes
    nonce, ct = raw[:12], raw[12:]  # slice the byte string to get the nonce and ciphertext
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ct, None)  # decrypts the ciphertext using the nonce and key
    return pt.decode('utf-8')