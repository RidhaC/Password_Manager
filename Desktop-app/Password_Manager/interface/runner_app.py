# interface/runner_app.py
"""
Runs the interface.
"""
import os, sys, tkinter as tk
from tkinter import PhotoImage
from .login_interface import build_login_frame
from .create_account_interface import build_create_account_frame
from .logged_in_interface import build_logged_in_frame
import customtkinter as ctk
from .autolock import setup_autolock, reset_autolock_timer

# Helper function to get resource path, works for dev and for PyInstaller
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class PassMan(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")       # "light" / "dark" / "system"
        ctk.set_default_color_theme("blue")   # "blue" / "green" / "dark-blue"

        # Updated app title and geometry
        self.title("Access Guardians Password Manager")
        self.geometry("380x420")

        # Updated logo loading logic
        try:
            # Try .ico first (for Windows)
            icon_path = resource_path("logo.ico")

            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            elif os.path.exists(icon_path):
                # use Tk PhotoImage, and keep a reference
                self._icon_image = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, self._icon_image)
            else:
                print("Icon not found in interface folder or parent directory.")
        except Exception as e:
            print("Icon load failed:", e)

        self.current_frame = None  # keeps track of current frame that is displayed

        # store widget handles so tests or future functions can interact with them if needed
        self._login = {}    # keeps track of login screen widgets
        self._create = {}   # keeps track of create account screen widgets
        self._logged_in = {}  # keeps track of logged in screen widgets

        self.show_login()  # shows the login screen when the app starts up
        setup_autolock(self, timeout_seconds=5 * 60)

    # Clears the current frame and resets relevant data
    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
        # reset only interface widgets, keep session data (like master_password)
        self._login = {}
        self._create = {}
        # do NOT reset self._logged_in here

    # Methods delegate to screen builders to preserve original behavior/comments
    def show_login(self):
        build_login_frame(self)

    def create_account_but(self):
        build_create_account_frame(self)

    def show_logged_in(self, username):
        # The logged-in screen now builds the vault itself; no extra calls needed.
        build_logged_in_frame(self, username)

        # Reset autolock timer on user interaction
        try:
            reset_autolock_timer(self)
        except Exception:
            pass


def run_interface():  # function to run the interface
    app = PassMan()  # creates an instance of the PassMan class to run with mainloop
    app.mainloop()  # starts the mainloop to run the application
