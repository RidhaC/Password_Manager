# main.py
"""

Entry point for the Password Manager desktop application.

This imports database.users to create a table and runs the Tkinter interface.

"""

# imports the database module to create or add users to the SQLite database
from database.users import database_create

# imports the interface runner to run the Tkinter user interface 
from interface.runner_app import run_interface 

# if the table does not currently exist then one will be created
database_create()

# this will pull up the users interface 
run_interface()

