"""
test_generator.py

in this test we will test the strength of the generated password.

We will use the functions generate_password and validate password to test the strength of 
the generated password.

# cd Password_Manager
# $env:PYTHONPATH="."
# pytest pytest/test_generator.py


"""

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import interface

def test_generate_password_strength():
    pwd = interface.generate_password(16) # generates a password with the length of 16
    pwd2 = "weak"
    ok, missing = interface.validate_password(pwd) # uses validate_password to validate the generated password
    ok2, missing2 = interface.validate_password(pwd2)
    assert ok, f"Generated password missing: {missing}" # ok will either return true or false while missing will tell you what was missing from your strong password
    assert ok2, f"Generated password missing: {missing2}"
    assert len(pwd) >= 16 # test to see if the password is 16 characters long
    assert len(pwd2) >= 16 