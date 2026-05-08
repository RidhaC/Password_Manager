"""
test_create_user.py

In this test we will test for the validation of a successful create creation and adding the 
account to the tempary file.

we will create a temp file and then override the path 
then we will define the username 
then we will generate the password 
then we will check to make sure the passwords equal each other 
then we will check the generated password for strength
then will test to see if an account was successfully created 


# cd Password_Manager
# $env:PYTHONPATH="."
# pytest pytest/test_create_user.py

"""

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import tempfile
import database
import interface

def test_create_user():
    fd, path = tempfile.mkstemp(prefix="temp_users", suffix=".db") # creates out temp file called temp_login.db
    os.close(fd) # closes the file descriptor 
    database.database_path = path # temporarily override the account.db in config
    database.datebase_create() # creates the temp database

    username = "I_think_Ridha_is_our_leader" # defines the username
    pwd1 = interface.generate_password(20) # generates a password with length of 20
    pwd2 = pwd1 # creates the same password to match with
    assert pwd1 == pwd2 #checks to see if the passowrds match 

    ok, missing = interface.validate_password(pwd1) # uses validate_password to validate the generated password
    assert ok, f"Password should be strong, missing: {missing}" # ok will either return true or false while missing will tell you what was missing from your strong password
    assert database.create_user(username, pwd1) is True # addes the user info to the create_user to see if it returns true

    try:
        os.remove(path) # removes the temp file
    except Exception:
        pass
