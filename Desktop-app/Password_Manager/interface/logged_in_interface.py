"""
Logged-in screen builder for the Password Manager app.
Handles password list, add/edit/delete functionality, and layout.
"""

import tkinter as tk
import customtkinter as ctk
from database.vault import save_secret, get_secrets, delete_secret, update_secret
from .alerts import build_alerts_frame
from .interface_functions import generate_password, password_strength_score

# Logout function
def _logout_user(app):
    app._logged_in = {}
    app.show_login()

# Attach password generator to an entry field
def attach_password_generator(parent, target_entry):
    import tkinter as tk
    import customtkinter as ctk

    # Password generator UI components
    gen_row = ctk.CTkFrame(parent)
    gen_row.pack(fill="x", pady=(6, 0))

    # Password length label and entry
    ctk.CTkLabel(gen_row, text="Length (min 16):").grid(row=0, column=0, sticky="w", padx=(5, 0))
    length_var = tk.StringVar(value="16")
    length_entry = ctk.CTkEntry(gen_row, width=70, textvariable=length_var)
    length_entry.grid(row=0, column=1, padx=(6, 10), pady=(2, 2))

    # Generate button function
    def do_generate():
        try:
            length = int(length_var.get())
        except ValueError:
            length = 16
        # enforce minimum length
        pwd = generate_password(length)

        # insert generated password into target entry
        prev_state = target_entry.cget("state")
        if prev_state == "readonly":
            target_entry.configure(state="normal")

        # insert generated password into target entry
        target_entry.delete(0, "end")
        target_entry.insert(0, pwd)

        # restore readonly state if applicable
        if prev_state == "readonly":
            target_entry.configure(state="readonly")

        try:
            target_entry.event_generate("<KeyRelease>")
        except Exception:
            pass

    # Generate button
    ctk.CTkButton(
        gen_row, text="Generate strong password", command=do_generate
    ).grid(row=0, column=2, padx=(4, 4), pady=(2, 2))

# Build the logged-in interface
def build_logged_in_frame(app, username):
    app.clear_frame()
    frame = ctk.CTkFrame(app, corner_radius=12)
    frame.pack(expand=True, fill="both", padx=20, pady=20)
    app.current_frame = frame

    frame.grid_rowconfigure(4, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # Header
    ctk.CTkLabel(frame, text=f"Hello, {username}!", font=("Helvetica", 16)).grid(row=0, column=0, pady=(0, 6))
    ctk.CTkLabel(frame, text="You are logged in.").grid(row=1, column=0)

    # --- Logout + Alerts row ---
    top_buttons = ctk.CTkFrame(frame)
    top_buttons.grid(row=2, column=0, pady=(10, 10))
    top_buttons.grid_columnconfigure((0, 1), weight=1)

    # Logout button and Alerts button
    logout_btn = ctk.CTkButton(top_buttons, text="Logout", command=lambda: _logout_user(app), height=28)
    logout_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

    alerts_btn = ctk.CTkButton(
        top_buttons,
        text="Alerts",
        command=lambda: build_alerts_frame(app, username),
        fg_color="#1e88e5",
        height=28
    )
    alerts_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    # Password list title
    ctk.CTkLabel(frame, text="Your Stored Passwords", font=("Helvetica", 14, "bold")).grid(row=3, column=0, pady=(5, 6))

    # Password list area
    list_frame = ctk.CTkScrollableFrame(frame, corner_radius=10)
    list_frame.grid(row=4, column=0, padx=5, pady=(0, 8), sticky="nsew")

    # Bottom button row
    btn_row = ctk.CTkFrame(frame)
    btn_row.grid(row=5, column=0, pady=(8, 0), sticky="sew")
    btn_row.grid_columnconfigure((0, 1), weight=1)

    # Get master password
    master_pw = getattr(app._logged_in, "get", lambda k, d=None: None)("master_password")
    if not master_pw:
        ctk.CTkLabel(list_frame, text="(No master password in session — please log in again.)").pack(pady=20)
        return

    # --- Refresh password list ---
    def refresh_list():
        for widget in list_frame.winfo_children():
            widget.destroy()
        secrets = get_secrets(username, master_pw)
        if not secrets:
            ctk.CTkLabel(list_frame, text="(No passwords stored yet.)").pack(pady=20)
        else:
            for s in secrets:
                entry_btn = ctk.CTkButton(
                    list_frame,
                    text=s["label"],
                    anchor="w",
                    fg_color="#2b2b2b",
                    hover_color="#3b3b3b",
                    command=lambda sec=s: show_password_details(app, username, master_pw, sec)
                )
                entry_btn.pack(fill="x", padx=5, pady=3)
                
    # --- Add Password Popup ---
    def add_password_popup():
        popup = ctk.CTkToplevel(app)
        popup.title("Add New Password")
        popup.geometry("480x520")
        popup.minsize(420, 400)
        popup.grab_set()
        popup.resizable(True, True)

        ctk.CTkLabel(popup, text="Add New Password", font=("Helvetica", 16, "bold")).pack(pady=(15, 5))
        content_frame = ctk.CTkScrollableFrame(popup, corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(content_frame, text="Label / Website:").pack(anchor="w", pady=(5, 0))
        label_entry = ctk.CTkEntry(content_frame)
        label_entry.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(content_frame, text="Account Username:").pack(anchor="w", pady=(5, 0))
        user_entry = ctk.CTkEntry(content_frame)
        user_entry.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(content_frame, text="Password:").pack(anchor="w", pady=(5, 0))
        pass_entry = ctk.CTkEntry(content_frame, show="•")
        pass_entry.pack(fill="x", pady=(0, 2))

        # --- Show Password toggle ---
        def toggle_password_visibility():
            if pass_entry.cget("show") == "•":
                pass_entry.configure(show="")
                show_btn.configure(text="Hide Password")
            else:
                pass_entry.configure(show="•")
                show_btn.configure(text="Show Password")

        show_btn = ctk.CTkButton(content_frame, text="Show Password", command=toggle_password_visibility, fg_color="gray25", height=25)
        show_btn.pack(anchor="e", pady=(0, 5))

        strength_label = ctk.CTkLabel(content_frame, text="Strength: ")
        strength_label.pack(anchor="w", pady=(4, 0))

        def _update_strength(_event=None):
            pwd = pass_entry.get()
            if not pwd.strip():
                strength_label.configure(text="Strength: ", text_color="white")
                return
            score, label = password_strength_score(pwd)
            color = {"Weak": "red", "Medium": "orange", "Strong": "green"}[label]
            strength_label.configure(text=f"Strength: {label} — {score:.1f}%", text_color=color)

        pass_entry.bind("<KeyRelease>", _update_strength)

        attach_password_generator(content_frame, pass_entry)

        ctk.CTkLabel(content_frame, text="URL (optional):").pack(anchor="w", pady=(5, 0))
        url_entry = ctk.CTkEntry(content_frame)
        url_entry.pack(fill="x", pady=(0, 5))


        ctk.CTkLabel(content_frame, text="Notes (optional):").pack(anchor="w", pady=(5, 0))
        notes_box = ctk.CTkTextbox(content_frame, height=100)
        notes_box.pack(fill="x", pady=(0, 5))

        status_label = ctk.CTkLabel(content_frame, text="", text_color="gray")
        status_label.pack(pady=(4, 0))

        # -- Save and Close function --
        def save_and_close():
            label = label_entry.get().strip()
            acc_user = user_entry.get().strip()
            acc_pass = pass_entry.get().strip()
            url = url_entry.get().strip()
            notes = notes_box.get("1.0", "end").strip()
            if not label or not acc_user or not acc_pass:
                status_label.configure(text="All required fields must be filled.", text_color="orange")
                return
            ok = save_secret(username, master_pw, label, acc_user, acc_pass, url, notes)
            if ok:
                status_label.configure(text=f"Password for '{label}' saved successfully.", text_color="green")
                popup.after(800, lambda: (popup.destroy(), refresh_list()))
            else:
                status_label.configure(text="Failed to save password.", text_color="red")

        btn_row_popup = ctk.CTkFrame(popup)
        btn_row_popup.pack(fill="x", pady=(5, 10), padx=15)
        ctk.CTkButton(btn_row_popup, text="Save", command=save_and_close).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_row_popup, text="Cancel", command=popup.destroy, fg_color="gray25").pack(side="left", expand=True, fill="x", padx=(5, 0))

    # --- Bottom Buttons ---
    add_btn = ctk.CTkButton(btn_row, text="Add Password", command=add_password_popup)
    add_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
    refresh_btn = ctk.CTkButton(btn_row, text="Refresh", command=refresh_list, fg_color="gray25")
    refresh_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

    refresh_list()

# Show password details
def show_password_details(app, username, master_pw, secret):
    """Display selected password details inline within the main window."""
    app.clear_frame()

    frame = ctk.CTkFrame(app, corner_radius=12)
    frame.pack(expand=True, fill="both", padx=20, pady=20)
    app.current_frame = frame

    # Configure layout
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # --- Back button ---
    ctk.CTkButton(
        frame,
        text="← Back",
        command=lambda: build_logged_in_frame(app, username),
        fg_color="gray25"
    ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

    # --- Header ---
    ctk.CTkLabel(frame, text=f"Details for {secret['label']}", font=("Helvetica", 18, "bold")).grid(row=1, column=0, pady=(5, 10))

    # --- Scrollable details ---
    detail_frame = ctk.CTkScrollableFrame(frame, corner_radius=10)
    detail_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

    def add_row(label, value):
        ctk.CTkLabel(detail_frame, text=f"{label}:", font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(8, 0), padx=10)
        ctk.CTkLabel(detail_frame, text=value or "(empty)", font=("Consolas", 12)).pack(anchor="w", padx=20)

    # --- Reordered: Username -> Password -> URL -> Notes ---
    add_row("Account Username", secret.get("account_username"))

    # --- Password Field ---
    ctk.CTkLabel(detail_frame, text="Password:", font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(8, 0), padx=10)
    pass_entry = ctk.CTkEntry(detail_frame, show="•")
    pass_entry.insert(0, secret.get("password", ""))
    pass_entry.configure(state="readonly")
    pass_entry.pack(fill="x", padx=20, pady=(0, 5))

    def toggle_pw_visibility():
        if pass_entry.cget("show") == "•":
            pass_entry.configure(show="")
            toggle_btn.configure(text="Hide Password")
        else:
            pass_entry.configure(show="•")
            toggle_btn.configure(text="Show Password")

    toggle_btn = ctk.CTkButton(detail_frame, text="Show Password", command=toggle_pw_visibility, fg_color="gray25", height=25)
    toggle_btn.pack(anchor="e", padx=20, pady=(0, 10))

    # --- URL and Notes ---
    add_row("URL", secret.get("url"))
    add_row("Notes", secret.get("notes"))

    # --- Delete & Edit buttons ---
    btn_frame = ctk.CTkFrame(frame)
    btn_frame.grid(row=3, column=0, pady=(10, 10), sticky="ew")
    btn_frame.grid_columnconfigure((0, 1), weight=1)

    # --- Delete Fix ---
    def confirm_delete():
        ok = delete_secret(username, master_pw, secret["label"])
        msg = "Deleted successfully." if ok else "Failed to delete."
        color = "green" if ok else "red"
        ctk.CTkLabel(frame, text=msg, text_color=color).grid(row=4, column=0)
        if ok:
            frame.after(800, lambda: build_logged_in_frame(app, username))

    # --- Inline Edit Mode ---
    def edit_entry():
        """Turn the details view into an inline edit mode (no popup)."""
        for widget in frame.winfo_children():
            widget.destroy()

        # Back button
        ctk.CTkButton(
            frame, text="← Back",
            command=lambda: show_password_details(app, username, master_pw, secret),
            fg_color="gray25"
        ).pack(anchor="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(frame, text=f"Editing {secret['label']}", font=("Helvetica", 18, "bold")).pack(pady=(5, 10))

        # Editable fields
        edit_frame = ctk.CTkScrollableFrame(frame, corner_radius=10)
        edit_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(edit_frame, text="Account Username:").pack(anchor="w")
        user_entry = ctk.CTkEntry(edit_frame)
        user_entry.insert(0, secret["account_username"] or "")
        user_entry.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(edit_frame, text="Password:").pack(anchor="w")
        pass_entry = ctk.CTkEntry(edit_frame, show="•")
        pass_entry.insert(0, secret["password"] or "")
        pass_entry.pack(fill="x", pady=(0, 5))

        # Password visibility toggle
        def toggle_pw():
            if pass_entry.cget("show") == "•":
                pass_entry.configure(show="")
                toggle_btn.configure(text="Hide Password")
            else:
                pass_entry.configure(show="•")
                toggle_btn.configure(text="Show Password")

        toggle_btn = ctk.CTkButton(edit_frame, text="Show Password", command=toggle_pw, fg_color="gray25", height=25)
        toggle_btn.pack(anchor="e", pady=(0, 5))

        edit_strength_label = ctk.CTkLabel(edit_frame, text="Strength: ")
        edit_strength_label.pack(anchor="w", pady=(4, 0))

        def _edit_update_strength(_event=None):
            pwd = pass_entry.get()
            if not pwd.strip():
                edit_strength_label.configure(text="Strength: ", text_color="white")
                return
            score, label = password_strength_score(pwd)
            color = {"Weak": "red", "Medium": "orange", "Strong": "green"}[label]
            edit_strength_label.configure(text=f"Strength: {label} — {score:.1f}%", text_color=color)

        pass_entry.bind("<KeyRelease>", _edit_update_strength)

        attach_password_generator(edit_frame, pass_entry)

        ctk.CTkLabel(edit_frame, text="URL:").pack(anchor="w")
        url_entry = ctk.CTkEntry(edit_frame)
        url_entry.insert(0, secret["url"] or "")
        url_entry.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(edit_frame, text="Notes:").pack(anchor="w")
        notes_box = ctk.CTkTextbox(edit_frame, height=100)
        notes_box.insert("1.0", secret["notes"] or "")
        notes_box.pack(fill="x", pady=(0, 10))

        status_label = ctk.CTkLabel(edit_frame, text="", text_color="gray")
        status_label.pack(pady=(0, 10))

        def save_changes():
            new_user = user_entry.get().strip()
            new_pass = pass_entry.get().strip()
            new_url = url_entry.get().strip()
            new_notes = notes_box.get("1.0", "end").strip()

            ok = update_secret(username, master_pw, secret["label"], new_user, new_pass, new_url, new_notes)
            if ok:
                status_label.configure(text="Changes saved successfully.", text_color="green")
                frame.after(800, lambda: build_logged_in_frame(app, username))
            else:
                status_label.configure(text="Failed to update entry.", text_color="red")

        # Save/Cancel Buttons
        btn_row = ctk.CTkFrame(frame)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkButton(btn_row, text="Save", command=save_changes, fg_color="#2b6cb0").pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_row, text="Cancel", command=lambda: show_password_details(app, username, master_pw, secret), fg_color="gray25").pack(side="left", expand=True, fill="x", padx=(5, 0))

    # --- Buttons Row ---
    ctk.CTkButton(btn_frame, text="Edit", command=edit_entry, fg_color="#2b6cb0").grid(row=0, column=0, sticky="ew", padx=5)
    ctk.CTkButton(btn_frame, text="Delete", command=confirm_delete, fg_color="red4", hover_color="darkred").grid(row=0, column=1, sticky="ew", padx=5)
