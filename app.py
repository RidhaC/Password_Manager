# app.py

import os
import pyotp
import threading
import webbrowser
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database.users import (
    database_create, create_user, user_verification,
    get_user_totp_secretkey, set_2fa_enabled
)
from database.vault import save_secret, get_secrets, delete_secret, update_secret
from database.LO_BC import (
    is_user_locked, register_failed_attempt, reset_attempts,
    generate_backup_codes, store_backup_codes, consume_backup_code,
    remaining_backup_count
)
import qrcode, io, base64

app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True


def _qr_base64(uri):
    buf = io.BytesIO()
    qrcode.make(uri).resize((200, 200)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── Auth guard ──────────────────────────────────────────────
def logged_in():
    return session.get("username") and session.get("master_password")


# ── Routes ──────────────────────────────────────────────────

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
        return jsonify({"error": f"Account locked. Try again in {mm:02d}:{ss:02d}."}), 403

    if not user_verification(u, p):
        remaining = register_failed_attempt(u, max_attempts=5, lockout_seconds=300)
        msg = f"Invalid credentials. {remaining} attempt(s) remaining." if remaining > 0 else "Account locked."
        return jsonify({"error": msg}), 401

    reset_attempts(u)
    session["pending_user"] = u
    session["pending_password"] = p
    return jsonify({"next": "otp"})


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    u = session.get("pending_user")
    p = session.get("pending_password")
    if not u:
        return jsonify({"error": "Session expired."}), 401

    data = request.json
    code = data.get("code", "").strip()
    use_backup = data.get("backup", False)

    secretkey = get_user_totp_secretkey(u)

    if use_backup:
        if not consume_backup_code(u, code):
            return jsonify({"error": "Backup code invalid or already used."}), 401
    else:
        if not pyotp.TOTP(secretkey).verify(code):
            return jsonify({"error": "Invalid code. Try again."}), 401

    session.clear()
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
        return jsonify({"error": "Username already exists."}), 409
    if p != c:
        return jsonify({"error": "Passwords do not match."}), 400
    if len(p) < 16:
        return jsonify({"error": "Password must be at least 16 characters."}), 400

    success = create_user(u, p)
    if not success:
        return jsonify({"error": "Account creation failed. Try a different username."}), 500

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
        return jsonify({"error": "Session expired."}), 401

    code = request.json.get("code", "").strip()
    if not pyotp.totp.TOTP(secretkey).verify(code):
        return jsonify({"error": "Invalid code. Try again."}), 401

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
    secrets = get_secrets(session["username"], session["master_password"])
    return jsonify(secrets)


@app.route("/api/secrets", methods=["POST"])
def api_add_secret():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    d = request.json
    ok = save_secret(
        session["username"], session["master_password"],
        d.get("label", ""), d.get("account_username", ""),
        d.get("password", ""), d.get("url", ""), d.get("notes", "")
    )
    return jsonify({"ok": ok})


@app.route("/api/secrets/<int:sid>", methods=["PUT"])
def api_update_secret(sid):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    d = request.json
    ok = update_secret(
        session["username"], session["master_password"],
        d.get("old_label"), d.get("account_username"),
        d.get("password"), d.get("url"), d.get("notes")
    )
    return jsonify({"ok": ok})


@app.route("/api/secrets/delete", methods=["POST"])
def api_delete_secret():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    label = request.json.get("label")
    ok = delete_secret(session["username"], session["master_password"], label)
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