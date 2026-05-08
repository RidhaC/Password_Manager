# Access Guardians - Password Manager

A secure local desktop password manager built with Python, Flask, and Electron.

## Prerequisites

- Python 3.x
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

**3 - Install Electron dependencies:**
```bash
cd electron-app
npm install
```

**4 - Run the app:**
```bash
npm start
```

This starts the Flask backend and opens the app window automatically.

## Creating a Desktop Shortcut (Windows)

After setup, right click `electron-app/AccessGuardians.vbs` and click **Create Shortcut**, then move the shortcut to your desktop. Right click the shortcut, go to Properties, Change Icon, and point it to `electron-app/logo.ico`.

## Security

- All passwords are encrypted with AES-256-GCM
- Master password is never stored
- TOTP two-factor authentication required on every login
- Brute-force lockout after 5 failed attempts
- Backup codes for account recovery