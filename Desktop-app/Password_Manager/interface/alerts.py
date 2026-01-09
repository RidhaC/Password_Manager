"""
Alerts screen for password change reminders.
Shows alerts when stored passwords have not been updated for 6 months.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.vault import get_all_credentials
import tkinter.messagebox as messagebox


def build_alerts_frame(app, username):
    """Creates the Alerts screen with both password age and duplicate alerts."""
    app.clear_frame()
    frame = ctk.CTkFrame(app)
    frame.pack(expand=True, fill="both", padx=20, pady=20)
    app.current_frame = frame

    ctk.CTkLabel(frame, text="Password Alerts", font=("Segoe UI", 20, "bold")).pack(pady=(5, 15))

    try:
        credentials = get_all_credentials(username, app._logged_in.get("master_password"))
        now = datetime.now()
        alerts_found = False
        seen_passwords = {}

        # --- Password age alerts (6 months old) ---
        for cred in credentials:
            site = cred.get("label", "Unknown Site")
            last_updated = cred.get("last_updated")
            if last_updated:
                try:
                    last_updated = datetime.fromisoformat(last_updated)
                except Exception:
                    continue

                if now - last_updated > timedelta(days=180):
                    alerts_found = True
                    ctk.CTkLabel(
                        frame,
                        text=f"Password for {site} has not been updated in over 6 months.",
                        wraplength=320,
                        text_color="orange"
                    ).pack(pady=3)

            # Build dictionary for duplicate detection
            pw = cred.get("password")
            if pw:
                seen_passwords.setdefault(pw, []).append(site)

        # --- Duplicate password alerts ---
        for pw, sites in seen_passwords.items():
            if len(sites) > 1:
                alerts_found = True
                joined = ", ".join(sites)
                ctk.CTkLabel(
                    frame,
                    text=f"Passwords for {joined} are identical. Consider changing one.",
                    wraplength=320,
                    text_color="#ff6666"
                ).pack(pady=3)

        if not alerts_found:
            ctk.CTkLabel(frame, text="No alerts. All passwords are unique and up to date!", text_color="green").pack(pady=10)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load alerts: {e}")

    ctk.CTkButton(frame, text="Back", command=lambda: app.show_logged_in(username)).pack(pady=15)
