"""
test_logout.py

test to see if the logout button successfully logs out the user 

We will activate the interface 
then we will simulate the login with a user
then we will click the logout button 
then we will verify if we have returned to the login page

# cd Password_Manager
# $env:PYTHONPATH="."
# pytest pytest/test_logout.py


"""

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import tkinter as tk
import interface


def test_logout():
    try:
        app = interface.PassMan() # runs the interface 
    except tk.TclError: # expects that the window doesn't open for the test
        return # skip the test silently
    try:
        app.show_logged_in("team_loves_pizza") # simulates a logged in user

        app._logged_in["logout_btn"].invoke() # clicks the logout button

        texts = [] # used to store text from the login page
        for child in app.current_frame.winfo_children(): 
            if isinstance(child, tk.Label):
                texts.append(child.cget("text")) # appends the text on the window to texts 
        assert "Login" in texts # checks to see if login is in the texts array
    finally:
        app.destroy() # shuts down the interface
