# database/connection.py
"""
Handles database connections.
"""
import sqlite3
from config.settings import database_path

def get_connection():
    # connects to the database file specified in config/settings.py
    # if it does not exist it will create one
    return sqlite3.connect(database_path)