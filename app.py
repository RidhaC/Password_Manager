# app.py

import os
import pyotp
import threading
import webbrowser
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database.users import (
    database_create, create_user, user_verification,
    get_user_totp_secretkey, set_2fa_enabled,
    get_user_profile, update_user_profile, update_user_password,
    update_user_theme, get_custom_categories, add_custom_category,
    delete_custom_category
)
from database.vault import save_secret, get_secrets, delete_secret, update_secret, mark_secret_used, get_password_history
from database.LO_BC import (
    is_user_locked, register_failed_attempt, reset_attempts,
    generate_backup_codes, store_backup_codes, consume_backup_code,
    remaining_backup_count
)
import qrcode, io, base64
from collections import defaultdict
import time as _time

_api_hits = defaultdict(list)
API_LIMIT = 60
API_WINDOW = 60

def _api_rate_ok():
    key = session.get("username", "anon")
    now = _time.time()
    hits = [t for t in _api_hits[key] if now - t < API_WINDOW]
    hits.append(now)
    _api_hits[key] = hits
    return len(hits) <= API_LIMIT

from database.session import mark_2fa_verified, is_2fa_recent, clear_2fa_session
from database.connection import get_connection

app = Flask(__name__)
_key_file = os.path.join(os.path.dirname(__file__), 'electron-app', '.secret_key')
if os.path.exists(_key_file):
    with open(_key_file, 'rb') as f:
        _secret = f.read()
else:
    _secret = os.urandom(32)
    with open(_key_file, 'wb') as f:
        f.write(_secret)
app.secret_key = _secret
app.config["SESSION_COOKIE_HTTPONLY"] = True

from datetime import timedelta
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=20)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

def _qr_base64(uri):
    buf = io.BytesIO()
    qrcode.make(uri).resize((200, 200)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def logged_in():
    return session.get("username") and session.get("master_password")



@app.route("/")
def index():
    if logged_in():
        return redirect(url_for("vault"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    data = request.json
    u = data.get("username", "").strip()
    p = data.get("password", "")
    locked, seconds = is_user_locked(u)
    if locked:
        mm, ss = divmod(seconds, 60)
        return jsonify({"error": f"Account locked. Try again in {mm:02d}:{ss:02d}"}), 403
    if not user_verification(u, p):
        remaining = register_failed_attempt(u, max_attempts=5, lockout_seconds=300)
        if remaining == 0 and is_user_locked(u)[0]:
            msg = "Account locked. Too many failed attempts."
        else:
            msg = f"Invalid credentials. {remaining} attempt(s) remaining" if remaining > 0 else "Incorrect Username or Password"
        return jsonify({"error": msg}), 401
    reset_attempts(u)
    connect = get_connection()
    cur = connect.cursor()
    cur.execute("SELECT username FROM accounts WHERE email = ?", (u,))
    row = cur.fetchone()
    if row:
        u = row[0]
    connect.close()
    if is_2fa_recent(u):
        session.permanent = True
        session["username"] = u
        session["master_password"] = p
        return jsonify({"next": "vault"})
    session["pending_user"] = u
    session["pending_password"] = p
    return jsonify({"next": "otp"})


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    u = session.get("pending_user")
    p = session.get("pending_password")
    if not u:
        return jsonify({"error": "Session expired"}), 401

    data = request.json
    code = data.get("code", "").strip()
    use_backup = data.get("backup", False)

    secretkey = get_user_totp_secretkey(u)

    if use_backup:
        if not consume_backup_code(u, code):
            return jsonify({"error": "Backup code invalid or already used"}), 401
    else:
        if not pyotp.TOTP(secretkey).verify(code):
            return jsonify({"error": "Invalid code. Try again"}), 401

    mark_2fa_verified(u)
    session.clear()
    session.permanent = True
    session["username"] = u
    session["master_password"] = p
    return jsonify({"next": "/vault"})


@app.route("/create-account", methods=["GET", "POST"])
def create_account():
    if request.method == "GET":
        return render_template("create_account.html")

    data = request.json
    u = data.get("username", "").strip()
    p = data.get("password", "")
    c = data.get("confirm", "")

    if get_user_totp_secretkey(u) is not None:
        return jsonify({"error": "Username already exists"}), 409
    if p != c:
        return jsonify({"error": "Passwords do not match"}), 400
    if len(p) < 16:
        return jsonify({"error": "Password must be at least 16 characters"}), 400

    success = create_user(u, p)
    if not success:
        return jsonify({"error": "Account creation failed. Try a different username"}), 500

    secretkey = get_user_totp_secretkey(u)
    uri = pyotp.totp.TOTP(secretkey).provisioning_uri(name=u, issuer_name="Access Guardians")
    qr_img = _qr_base64(uri)

    session["setup_user"] = u
    session["setup_secret"] = secretkey
    return jsonify({"qr": qr_img, "next": "setup_2fa"})


@app.route("/setup-2fa", methods=["POST"])
def setup_2fa():
    u = session.get("setup_user")
    secretkey = session.get("setup_secret")
    if not u:
        return jsonify({"error": "Session expired"}), 401

    code = request.json.get("code", "").strip()
    if not pyotp.totp.TOTP(secretkey).verify(code):
        return jsonify({"error": "Invalid code. Try again"}), 401

    set_2fa_enabled(u, True)
    plain = generate_backup_codes(n=10, length=10)
    store_backup_codes(u, plain)
    session.pop("setup_user", None)
    session.pop("setup_secret", None)
    return jsonify({"backup_codes": plain})


@app.route("/vault")
def vault():
    if not logged_in():
        return redirect(url_for("login"))
    return render_template("vault.html", username=session["username"])


@app.route("/api/secrets", methods=["GET"])
def api_get_secrets():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    if not _api_rate_ok():
        return jsonify({"error": "Too many requests."}), 429
    sort_by = request.args.get('sort', 'last_used')
    secrets = get_secrets(session["username"], session["master_password"], sort_by=sort_by)
    return jsonify(secrets)

@app.route("/api/secrets", methods=["POST"])
def api_add_secret():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    if not _api_rate_ok():
        return jsonify({"error": "Too many requests"}), 429
    d = request.json
    ok = save_secret(
        session["username"], session["master_password"],
        d.get("label", ""), d.get("account_username", ""),
        d.get("password", ""), d.get("url", ""), d.get("notes", ""),
        d.get("category", "other")
    )
    return jsonify({"ok": ok})

@app.route("/api/secrets/<int:sid>", methods=["PUT"])
def api_update_secret(sid):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    if not _api_rate_ok():
        return jsonify({"error": "Too many requests"}), 429
    d = request.json
    ok = update_secret(
        session["username"], session["master_password"],
        d.get("old_label"), d.get("label"), d.get("account_username"),
        d.get("password"), d.get("url"), d.get("notes"),
        d.get("category", "other")
    )
    return jsonify({"ok": ok})


@app.route("/api/secrets/delete", methods=["POST"])
def api_delete_secret():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    if not _api_rate_ok():
        return jsonify({"error": "Too many requests."}), 429
    label = request.json.get("label")
    ok = delete_secret(session["username"], session["master_password"], label)
    return jsonify({"ok": ok})

@app.route("/api/secrets/used", methods=["POST"])
def api_mark_used():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    label = request.json.get("label")
    ok = mark_secret_used(session["username"], session["master_password"], label)
    return jsonify({"ok": ok})

@app.route("/api/secrets/history", methods=["POST"])
def api_get_history():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    label = request.json.get("label")
    history = get_password_history(session["username"], session["master_password"], label)
    return jsonify(history)

@app.route("/settings")
def settings():
    if not logged_in():
        return redirect(url_for("login"))
    profile = get_user_profile(session["username"])
    cats = get_custom_categories(session["username"])
    return render_template("settings.html", username=session["username"], profile=profile, custom_categories=cats)

@app.route("/api/settings/profile", methods=["POST"])
def api_update_profile():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    d = request.json
    ok = update_user_profile(session["username"], d.get("first_name",""), d.get("last_name",""), d.get("email",""))
    return jsonify({"ok": ok})

@app.route("/api/settings/password", methods=["POST"])
def api_update_password():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    d = request.json
    old_pw = d.get("old_password","")
    new_pw = d.get("new_password","")
    if len(new_pw) < 16:
        return jsonify({"error": "Password must be at least 16 characters"}), 400
    ok = update_user_password(session["username"], old_pw, new_pw)
    if not ok:
        return jsonify({"error": "Current password is incorrect"}), 401
    session["master_password"] = new_pw
    return jsonify({"ok": True})

@app.route("/api/settings/theme", methods=["POST"])
def api_update_theme():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    theme = request.json.get("theme", "dark")
    ok = update_user_theme(session["username"], theme)
    return jsonify({"ok": ok})

@app.route("/api/categories", methods=["GET"])
def api_get_categories():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_custom_categories(session["username"]))

@app.route("/api/categories", methods=["POST"])
def api_add_category():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    d = request.json
    ok = add_custom_category(session["username"], d.get("name",""), d.get("icon","📁"), d.get("color","#7c5cbf"))
    return jsonify({"ok": ok})

@app.route("/api/import", methods=["POST"])
def api_import():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    entries = request.json.get("entries", [])
    existing = get_secrets(session["username"], session["master_password"])
    pre_existing = {s["label"].strip().lower() for s in existing}
    imported = 0
    skipped = 0
    duplicates = 0
    for e in entries:
        label = e.get("label", "").strip()
        if label.lower() in pre_existing:
            duplicates += 1
            continue
        try:
            ok = save_secret(
                session["username"], session["master_password"],
                label, e.get("username", ""),
                e.get("password", ""), e.get("url", ""), e.get("notes", ""),
                "other"
            )
            if ok:
                imported += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1
    return jsonify({"ok": True, "imported": imported, "skipped": skipped, "duplicates": duplicates})

@app.route("/api/categories/<int:cid>", methods=["DELETE"])
def api_delete_category(cid):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    ok = delete_custom_category(session["username"], cid)
    return jsonify({"ok": ok})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    database_create()
    threading.Timer(1.0, open_browser).start()
    app.run(debug=False, port=5000)
    