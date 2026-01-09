# interface/autolock.py

"""
Autolock functionality for the Password Manager app.
This module sets up an automatic lock mechanism that logs out
the user after a period of inactivity.
"""
import tkinter as tk

DEFAULT_TIMEOUT_SEC = 5 * 60  # change as needed and needed to change in the runner_app.py to match

# Setup autolock functionality
def setup_autolock(app, timeout_seconds: int = DEFAULT_TIMEOUT_SEC):
    app._autolock_seconds = timeout_seconds
    app._autolock_after_id = None

    def _reset(_=None):
        reset_autolock_timer(app)

    for seq in ("<Key>", "<Motion>", "<Button>", "<MouseWheel>"):
        app.bind_all(seq, _reset, add="+")

    reset_autolock_timer(app)

# Reset the autolock timer
def reset_autolock_timer(app):
    cancel_autolock(app)
    ms = int(getattr(app, "_autolock_seconds", DEFAULT_TIMEOUT_SEC) * 1000)
    def _timeout():
        # Optionally clear any sensitive in-memory state here.
        try:
            app.show_login()
        except Exception:
            pass
    app._autolock_after_id = app.after(ms, _timeout)

# Cancel any existing autolock timer
def cancel_autolock(app):
    if getattr(app, "_autolock_after_id", None):
        try:
            app.after_cancel(app._autolock_after_id)
        except Exception:
            pass
    app._autolock_after_id = None
