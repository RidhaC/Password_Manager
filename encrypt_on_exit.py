import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from database.db_crypto import encrypt_db
encrypt_db()
print("DB encrypted.")
