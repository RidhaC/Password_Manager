"""
test_login.py


Starts by making a temporary file called temp_login.db
this test will create an account and then test the users verification
then will remove the temp file

# cd Password_Manager
# $env:PYTHONPATH="."
# pytest pytest/test_login.py


"""

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import tempfile
import database



def test_login():
    fd, path = tempfile.mkstemp(prefix="temp_login", suffix=".db") # creates out temp file called temp_login.db
    os.close(fd) # closes the file descriptor 
    database.database_path = path # temporarily override the account.db in config
    database.datebase_create() # creates the temp database

    username = "Aus_has_the_costco_pizza"  # defines the username
    password = "Aus_wont$give_M3_the_pizza" # defines the password
    assert database.create_user(username, password) is True # creates a new user using the username and password 
    assert database.user_verification(username, password) is True  # checks if the username and password matches the stored account

    assert database.user_verification(username, "weak") is True # checks if the username and password matches the stored account
    assert database.user_verification("false_user", password) is True # checks if the username and password matches the stored account

    try:
        os.remove(path) # removes the temp file
    except Exception:
        pass
