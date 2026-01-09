"""
Account creation screen builder.

"""
import tkinter as tk                 # kept this for compatibility
import customtkinter as ctk          # added this
import pyotp
import qrcode
import io
from PIL import Image, ImageTk
from tkinter import Toplevel, messagebox
from database.users import get_user_totp_secretkey, create_user, set_2fa_enabled
from .interface_functions import validate_password, generate_password, password_strength_score
from database.LO_BC import generate_backup_codes, store_backup_codes

mask = "•"  # this is our character that will be used to mask the password input

def build_create_account_frame(app):
    app.clear_frame()  # clears current frame
    frame = ctk.CTkFrame(app, corner_radius=12)
    frame.pack(expand=True, fill="both", padx=20, pady=20)

    app.current_frame = frame  # saves the current frame

    ctk.CTkLabel(frame, text="Create Account", font=("Helvetica", 16)).pack(pady=(0, 10))  # Create account header label

    ctk.CTkLabel(frame, text="Username").pack(anchor="w")  # label for username
    username_entry = ctk.CTkEntry(frame)  # entry for the username
    username_entry.pack(fill="x")  # expands the entry box horizontally

    ctk.CTkLabel(frame, text="Password").pack(anchor="w")  # label for password
    password_entry = ctk.CTkEntry(frame, show=mask)  # entry for the password with masked characters
    password_entry.pack(fill="x")  # expands the entry box horizontally

    strength_label = ctk.CTkLabel(frame, text="Strength: ")
    strength_label.pack(anchor="w", pady=(4, 0))

    def update_strength(event=None):
        # Update the password strength label live while typing.
        pwd = password_entry.get()
        if not pwd.strip():
            strength_label.configure(text="Strength: ", text_color="white")
            return
        score, label = password_strength_score(pwd)
        color = {"Weak": "red", "Medium": "orange", "Strong": "green"}[label]
        # Always refresh with formatted score
        strength_label.configure(text=f"Strength: {label} — {score:.1f}%", text_color=color)
        strength_label.update_idletasks()  # ensures UI refresh

    # Bind live typing updates
    password_entry.bind("<KeyRelease>", update_strength)

    ctk.CTkLabel(frame, text="Confirm Password").pack(anchor="w")  # label for confirming password
    confirm_entry = ctk.CTkEntry(frame, show=mask)  # confirm password entry with masked characters
    confirm_entry.pack(fill="x")  # expands the entry box horizontally

    # --- Password Generator Row ---
    gen_row = ctk.CTkFrame(frame)
    gen_row.pack(fill="x", pady=(10, 0))

    ctk.CTkLabel(gen_row, text="Length (min 16):").grid(row=0, column=0, sticky="w", padx=(5, 0))
    length_var = tk.StringVar(value="16")
    length_entry = ctk.CTkEntry(gen_row, width=70, textvariable=length_var)
    length_entry.grid(row=0, column=1, padx=(6, 10), pady=(2, 2))

    def do_generate():  # generates a strong password
        try:
            length = int(length_var.get())  # pulls the length from the entry box and converts it to an integer
        except ValueError:
            length = 16  # sets length to 16 if integer conversion fails
        pwd = generate_password(length)  # generates the password using the generate_password function
        password_entry.delete(0, tk.END)  # clears the password field
        confirm_entry.delete(0, tk.END)  # clears the confirm password field
        password_entry.insert(0, pwd)  # inserts the generated password into the password field
        confirm_entry.insert(0, pwd)  # inserts the generated password into the confirm password field
        update_strength()

    gen_btn = ctk.CTkButton(gen_row, text="Generate strong password", command=do_generate)
    gen_btn.grid(row=0, column=2, padx=(4, 4), pady=(2, 2))

    var_show = ctk.BooleanVar(value=False)  # checkbox that toggles password visibility

    def pass_show():  # function to show or hide the password
        s = "" if var_show.get() else mask  # empty string if true else mask character
        password_entry.configure(show=s)  # updates password field visibility
        confirm_entry.configure(show=s)  # updates confirm password field visibility

    show_cb = ctk.CTkCheckBox(frame, text="Show password", variable=var_show, command=pass_show)  # checkbox to show or hide the password
    show_cb.pack(anchor="w", pady=(6, 8))  # padding for checkbox

    def create_account():  # creates new account function
        u = username_entry.get().strip()  # gets the username and removes extra spaces
        p = password_entry.get()  # gets the password
        c = confirm_entry.get()  # grabs the confirmed password

        if get_user_totp_secretkey(u) is not None:  # checks if the username already exists in the database
            messagebox.showerror("Exists", "Username already exists. Choose another.")  # error for existing username
            return

        if not u or not p:  # if the fields are left empty run the error messages
            messagebox.showwarning("Missing", "Username and password required.")  # warning for empty fields
            return
        if p != c:  # if passwords do not match
            messagebox.showwarning("Mismatch", "Passwords do not match.")  # warning for passwords not matching
            return

        ok, missing = validate_password(p)  # checks if the password meets the new strength rules
        if not ok:  # if the password is weak
            messagebox.showwarning(  # shows warning message listing what is missing
                "Weak password",
                "Password does not meet requirements:\n - length ≥ 16\n - at least one uppercase\n - at least one lowercase\n - at least one symbol\n\nMissing: "
                + ", ".join(missing)
            )
            return
        # if get_user_totp_secretkey(u) is not None:  # checks if the username already exists in the database
        #     messagebox.showerror("Exists", "Username already exists. Choose another.")  # error for existing username
        #     return
        
        success = create_user(u, p)  # use the database module to create the user in the local machine
        if success:  # message for successful account creation
            secretkey = get_user_totp_secretkey(u)
            uri = pyotp.totp.TOTP(secretkey).provisioning_uri(name=u, issuer_name="Access Guardians Password Manager")
            #windowmf for qr code
            window= ctk.CTkToplevel(app)
            window.title("Scan QR Code for 2FA Setup")
            window.geometry("400x450")
            window.resizable(False, False)
            window.grab_set()  # to force user interaction with this window
            
            # Generate QR code
            # Generate and show QR code for TOTP setup
            buf = io.BytesIO()
            qr = qrcode.make(uri)
            qr = qr.resize((200, 200))
            qr.save(buf, format='PNG')
            buf.seek(0)
            display_image = Image.open(buf) # open image from bytes

            # UI
            ctk.CTkLabel(window, text="Scan this QR code with your Authenticator app:").pack(pady=10)
            qr_image = ImageTk.PhotoImage(display_image)
            qr_label = ctk.CTkLabel(window, image=qr_image, text="")
            qr_label.image = qr_image  # keep a reference
            qr_label.pack(pady=10)
            ctk.CTkLabel(window, text="Enter the code from your Authenticator app:").pack(pady=10)

            code_var= tk.StringVar()
            code_entry= ctk.CTkEntry(window, textvariable=code_var, width=150, justify="center")
            code_entry.pack(pady=10)

            # Remove the old messagebox line and replace it with:
            def verify_2fa():
                code= code_var.get().strip()
                if pyotp.totp.TOTP(secretkey).verify(code):
                    set_2fa_enabled(u, True)
                    display_image.close()
                    buf.close()
                # Close the QR code window
                    for x in window.winfo_children():
                        x.destroy()

                    plain = generate_backup_codes(n=10, length=10)
                    store_backup_codes(u, plain)

                    ctk.CTkLabel(window, text="2FA setup complete! These are your one-time backup codes:").pack(pady=8)
                    codes_box = ctk.CTkTextbox(window, height=150)
                    codes_box.pack(fill="x", padx=12)
                    codes_box.insert("1.0", "\n".join(plain))
                    codes_box.configure(state="disabled")

                    def save_to_txt():
                        import tkinter.filedialog as fd
                        path = fd.asksaveasfilename(
                            title="Save backup codes", defaultextension=".txt",
                            initialfile=f"{u}_backup_codes.txt")
                        if path:
                            with open(path, "w", encoding="utf-8") as f:
                                f.write("\n".join(plain))
                            messagebox.showinfo("Saved", "Backup codes saved.")

                    btn_row = ctk.CTkFrame(window); btn_row.pack(pady=10)
                    ctk.CTkButton(btn_row, text="Save to file", command=save_to_txt, fg_color="#2b6cb0").pack(side="left", padx=6)
                    ctk.CTkButton(btn_row, text="OK", command=lambda: [window.destroy(), app.show_login()]).pack(side="left", padx=6)
            
                else:
                    messagebox.showerror("Invalid", "Invalid 2FA code. Please try again.")

            verify_btn= ctk.CTkButton(window, text="Verify", command=verify_2fa)
            verify_btn.pack(pady=7)
            code_entry.focus_set()
            code_entry.bind("<Return>", lambda event: verify_2fa())

        else:  # message for failed account creation
            messagebox.showerror("Error", "Account creation failed. Try a different username.")  # error for failed account creation

    create_btn = ctk.CTkButton(frame, text="Create account", command=create_account)
    create_btn.pack(fill="x", pady=(6, 4))
    back_btn = ctk.CTkButton(frame, text="← Back to login", command=app.show_login)
    back_btn.pack(fill="x")

    # store widget references for future use or testing
    app._create = {
        "username": username_entry,
        "password": password_entry,
        "confirm": confirm_entry,
        "length_var": length_var,
        "length_entry": length_entry,
        "gen_btn": gen_btn,
        "show_var": var_show,
        "show_cb": show_cb,
        "create_btn": create_btn,
        "back_btn": back_btn,
    }
