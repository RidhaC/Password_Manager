# Access Guardians - Password Manager

A secure local desktop password manager built with Python, Flask, and Electron. Fully offline — your passwords never leave your machine.

## Features

- AES-256-GCM encryption on every stored field
- TOTP two-factor authentication required on every login
- Master password never stored — derived in memory only
- Brute-force lockout after 5 failed attempts
- Backup codes for account recovery
- Password categories, search, and security alerts
- Bulk delete with confirmation
- Password strength meter and generator
- Duplicate password and stale password detection

## Prerequisites

- Python 3.10+
- Node.js 18+

## Setup

**1 - Clone the repo:**
```bash
git clone https://github.com/RidhaC/Password_Manager.git
cd Password_Manager
```

**2 - Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**3 - Run the database migration** (adds category support):
```bash
python migrate.py
```

**4 - Install Electron dependencies:**
```bash
cd electron-app
npm install
```

**5 - Run the app:**
```bash
npm start
```

## Creating a Desktop Shortcut (Windows)

1. Right click `electron-app/AccessGuardians.vbs` and click **Create Shortcut**
2. Move the shortcut to your desktop
3. Right click the shortcut → Properties → Change Icon → point to `electron-app/logo.ico`
4. Right click the `.vbs` file → Properties → check **Unblock** to remove the security warning

## Project Structure

```
Password_Manager/
├── app.py                    ← Flask routes and API
├── main.py                   ← Flask server entry point
├── migrate.py                ← Database migration script
├── database/
│   ├── vault.py              ← AES-256 encrypted password storage
│   ├── users.py              ← User accounts and TOTP
│   ├── LO_BC.py              ← Lockout and backup codes
│   └── encryption.py         ← AES-GCM and key derivation
├── templates/                ← HTML pages
├── static/
│   ├── css/                  ← Modular stylesheets
│   └── js/                   ← Modular JavaScript
└── electron-app/
    ├── main.js               ← Electron window config
    ├── AccessGuardians.vbs   ← Windows launcher
    └── logo.ico              ← App icon
```

## Security Notes

- The SQLite database file (`vault_accounts.db`) is excluded from the repo via `.gitignore` - it contains your encrypted passwords
- Each field is individually encrypted with a unique nonce - identical passwords produce different ciphertext
- PBKDF2 with 200,000 iterations is used to derive the AES key from your master password
