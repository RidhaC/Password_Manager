"""
Login screen class and builder.

"""
import pyotp
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from database.users import user_verification
from database.users import get_user_totp_secretkey
from database.LO_BC import (is_user_locked, register_failed_attempt, reset_attempts,consume_backup_code)

mask = "•"  # this is our character that will be used to mask the password input

def build_login_frame(app):
    # how the login screen is built
    app.clear_frame()  # clears an exsisting frame
    frame = ctk.CTkFrame(app, corner_radius=12)
    frame.pack(expand=True, fill="both", padx=20, pady=20)  # packs the frame to fill the window
    app.current_frame = frame  # saves the current frame

    ctk.CTkLabel(frame, text="Login", font=("Helvetica", 16)).pack(pady=(0, 10))  # header label

    ctk.CTkLabel(frame, text="Username").pack(anchor="w")  # username label
    username_entry = ctk.CTkEntry(frame)  # entry box for the user to type their username
    username_entry.pack(fill="x")  # makes the entry go horizontally

    ctk.CTkLabel(frame, text="Password").pack(anchor="w")  # password label
    password_entry = ctk.CTkEntry(frame, show=mask)  # entry box for the user to type their password
    password_entry.pack(fill="x")  # makes the entry go horizontally

    var_show = ctk.BooleanVar(value=False)

    # function to toggle password visibility
    def pass_show():
        password_entry.configure(show="" if var_show.get() else mask)

    show_cb = ctk.CTkCheckBox(frame, text="Show password", variable=var_show, command=pass_show)
    show_cb.pack(anchor="w", pady=(2, 8))

    def login_but():  # login button function
        u = username_entry.get().strip()  # grabs the entered username and removes any extra spaces
        p = password_entry.get()  # grabs the entered password
        if not u or not p:  # check for empty fields
            messagebox.showwarning("Missing", "Enter username and password.")  # warning popup
            return  # stops the function if fields are empty

        # check if user is locked out
        locked, seconds = is_user_locked(u)
        if locked:
            mm, ss = divmod(seconds, 60)
            messagebox.showerror("Locked", f"Too many failed attempts. Try again in {mm:02d}:{ss:02d}.")
            return
        
        # verify username and password
        if not user_verification(u, p):
            remaining = register_failed_attempt(u, max_attempts=5, lockout_seconds=5*60)
            if remaining > 0:
                messagebox.showerror("Failed", f"Invalid username or password. Attempts left: {remaining}")
            else:
                messagebox.showerror("Locked", "Too many failed attempts. You are temporarily locked out.")
            return
        else:
            reset_attempts(u)
        
        secretkey = get_user_totp_secretkey(u)  # retrieves the user's TOTP secret key

        # Modern OTP popup before granting access
        otp_popup = ctk.CTkToplevel(app)
        otp_popup.title("Two-Factor Authentication")
        otp_popup.geometry("380x260")
        otp_popup.resizable(False, False)
        otp_popup.grab_set()

        # OTP instructions and entry
        ctk.CTkLabel(otp_popup, text="Enter your 6-digit TOTP code:", font=("Helvetica", 13)).pack(pady=(15, 5))
        otp_entry = ctk.CTkEntry(otp_popup, justify="center", font=("Consolas", 14))
        otp_entry.pack(pady=(5, 10))

        # status label for feedback
        status_label = ctk.CTkLabel(otp_popup, text="", text_color="gray")
        status_label.pack(pady=(0, 5))

        # function to use backup code
        def use_backup_code():
            code = otp_entry.get().strip()
            if not code:
                status_label.configure(text="Enter a backup code above.", text_color="orange")
                return
            if not consume_backup_code(u, code):
                status_label.configure(text="Backup code invalid or already used.", text_color="red")
                return
            otp_popup.destroy()
            if not hasattr(app, "_logged_in") or not isinstance(app._logged_in, dict):
                app._logged_in = {}
            app._logged_in["master_password"] = p
            app.show_logged_in(u)

        def verify_otp():  # verifies the OTP code entered by the user
            code = otp_entry.get().strip()
            if not code:
                status_label.configure(text="Please enter a code.", text_color="orange")
                return
            if not pyotp.TOTP(secretkey).verify(code):
                status_label.configure(text="Invalid code. Try again.", text_color="red")
                return

            # only after successful OTP verification
            otp_popup.destroy()
            
            # Modern welcome popup
            # welcome_popup = ctk.CTkToplevel(app)
            # welcome_popup.title("Welcome")
            # welcome_popup.geometry("300x160")
            # welcome_popup.resizable(False, False)
            # welcome_popup.grab_set()

            # ctk.CTkLabel(welcome_popup, text=f"Welcome, {u}!", font=("Helvetica", 15, "bold")).pack(pady=(30, 10))
            # ctk.CTkLabel(welcome_popup, text="Login successful.", text_color="gray70").pack()

            # def close_welcome():
            #     welcome_popup.destroy()
            #     app.show_logged_in(u)

            # ctk.CTkButton(welcome_popup, text="Continue", command=close_welcome).pack(pady=(20, 10))
            # welcome_popup.bind("<Return>", lambda e: close_welcome())


            # store master password safely
            if not hasattr(app, "_logged_in") or not isinstance(app._logged_in, dict):
                app._logged_in = {}
            app._logged_in["master_password"] = p

            # show logged-in screen after OTP verification
            app.show_logged_in(u)

        # buttons for verifying and canceling
        ctk.CTkButton(otp_popup, text="Verify", command=verify_otp).pack(pady=(5, 5))
        ctk.CTkButton(otp_popup, text="Use backup code", command=use_backup_code, fg_color="#2A7BD8", hover_color="#256ABC", text_color="white", height=30).pack(pady=(0, 5))
        ctk.CTkButton(otp_popup, text="Cancel", command=otp_popup.destroy, fg_color="gray25").pack()

        otp_entry.focus()
        otp_popup.bind("<Return>", lambda event: verify_otp())

    # buttons for login and create account
    login_btn = ctk.CTkButton(frame, text="Login", command=login_but)  # login button
    login_btn.pack(fill="x", pady=(6, 4))  # adds login button to the interface

    # create account button
    create_btn = ctk.CTkButton(frame, text="Create account →", command=app.create_account_but)  # create account button
    create_btn.pack(fill="x")  # adds the create account button to the interface

    # store widget references for future use or testing
    app._login = {
        "username": username_entry,
        "password": password_entry,
        "show_var": var_show,
        "show_cb": show_cb,
        "login_btn": login_btn,
        "create_btn": create_btn,
    }
