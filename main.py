# main.py
import threading
from app import app
from database.users import database_create

def run_flask():
    app.run(debug=False, port=5000, use_reloader=False)

if __name__ == "__main__":
    database_create()
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    flask_thread.join()