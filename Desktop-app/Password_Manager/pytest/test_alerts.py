import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime, timedelta

from database.users import database_create, create_user
from database.vault import save_secret, get_all_credentials
from database.connection import get_connection


TEST_USERNAME = "alerts_test_user"
TEST_PASSWORD = "AlertsTestPass!123"


def reset_test_user():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM accounts WHERE username = ?", (TEST_USERNAME,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
        cur.execute("DELETE FROM vault WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM accounts WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()


def setup_db_and_user():
    database_create()
    reset_test_user()
    ok = create_user(TEST_USERNAME, TEST_PASSWORD)
    assert ok, "Failed to create alerts test user"


def check_get_all_credentials_returns_last_updated():
    setup_db_and_user()

    # add 1 fresh secret
    ok = save_secret(
        TEST_USERNAME,
        TEST_PASSWORD,
        label="ExampleSite",
        account_username="user@example.com",
        password="P@ssw0rd!",
        url="https://example.com",
        notes="test entry",
    )
    assert ok, "Failed to save test secret"

    creds = get_all_credentials(TEST_USERNAME, TEST_PASSWORD)
    assert len(creds) == 1, "Expected exactly 1 credential"

    cred = creds[0]
    assert "last_updated" in cred, "Credential dict must have last_updated key"
    assert isinstance(cred["last_updated"], str), "last_updated should be an ISO datetime string"


def check_stale_and_duplicate_detection():
    setup_db_and_user()

    # fresh entry
    save_secret(
        TEST_USERNAME,
        TEST_PASSWORD,
        label="FreshSite",
        account_username="fresh@example.com",
        password="FreshPass!1",
        url="https://fresh.example.com",
        notes="",
    )

    # entry that we'll mark as stale
    save_secret(
        TEST_USERNAME,
        TEST_PASSWORD,
        label="OldSite",
        account_username="old@example.com",
        password="OldPass!1",
        url="https://old.example.com",
        notes="",
    )

    # two entries with the same password (duplicate)
    save_secret(
        TEST_USERNAME,
        TEST_PASSWORD,
        label="DupSite1",
        account_username="dup1@example.com",
        password="SamePass!123",
        url="https://dup1.example.com",
        notes="",
    )
    save_secret(
        TEST_USERNAME,
        TEST_PASSWORD,
        label="DupSite2",
        account_username="dup2@example.com",
        password="SamePass!123",
        url="https://dup2.example.com",
        notes="",
    )

    # Manually make OldSite older than ~6 months in the DB
    conn = get_connection()
    cur = conn.cursor()
    six_months_ago = datetime.now() - timedelta(days=6 * 30)
    cur.execute(
        """
        UPDATE vault
        SET last_updated = ?
        WHERE id IN (
            SELECT v.id
            FROM vault v
            JOIN accounts a ON v.user_id = a.id
            WHERE a.username = ? AND v.label = ?
        )
        """,
        (six_months_ago.isoformat(), TEST_USERNAME, "OldSite"),
    )
    conn.commit()
    conn.close()

    # Fetch credentials the same way alerts.py does
    creds = get_all_credentials(TEST_USERNAME, TEST_PASSWORD)

    # Duplicate + stale logic (mirrors alerts.py behavior)
    now = datetime.now()
    six_month_threshold = now - timedelta(days=180)

    # Stale: last_updated <= 6 months ago
    stale_labels = []
    password_groups = {}

    for c in creds:
        label = c["label"]
        # last_updated in vault is ISO string; convert to datetime
        try:
            last_updated_dt = datetime.fromisoformat(c["last_updated"])
        except Exception:
            continue

        if now - last_updated_dt > timedelta(days=180):
            stale_labels.append(label)

        pw = c["password"]
        password_groups.setdefault(pw, []).append(label)

    duplicate_groups = [
        labels for labels in password_groups.values() if len(labels) > 1
    ]

    # Expectations:
    assert "OldSite" in stale_labels, "OldSite should be detected as stale"

    found_dup_pair = any(
        "DupSite1" in group and "DupSite2" in group for group in duplicate_groups
    )
    assert found_dup_pair, "DupSite1 and DupSite2 should be detected as duplicates"


def run_all():
    tests = [
        ("Credentials include last_updated field", check_get_all_credentials_returns_last_updated),
        ("Stale + duplicate detection data is correct", check_stale_and_duplicate_detection),
    ]

    print("=== Running alerts tests ===")
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except AssertionError as e:
            print(f"[FAIL] {name}: {e}")
        except Exception as e:
            print(f"[ERROR] {name}: unexpected exception: {e}")

    reset_test_user()


if __name__ == "__main__":
    run_all()
