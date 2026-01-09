import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.users import database_create, create_user
from database.connection import get_connection
from database.LO_BC import (
    generate_backup_codes,
    store_backup_codes,
    remaining_backup_count,
    consume_backup_code,
)

TEST_USERNAME = "backup_codes_test_user"
TEST_PASSWORD = "BackupTestPass!123"


def reset_test_user():
    """Delete the test user (and related rows) so tests are repeatable."""
    conn = get_connection()
    cur = conn.cursor()

    # remove user & related rows if already present
    cur.execute("SELECT id FROM accounts WHERE username = ?", (TEST_USERNAME,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
        # these tables/columns must match your schema
        try:
            cur.execute("DELETE FROM backup_codes WHERE user_id = ?", (user_id,))
        except Exception:
            pass
        try:
            cur.execute("DELETE FROM lockouts WHERE user_id = ?", (user_id,))
        except Exception:
            pass
        try:
            cur.execute("DELETE FROM vault WHERE user_id = ?", (user_id,))
        except Exception:
            pass
        cur.execute("DELETE FROM accounts WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()


def setup_db_and_user():
    database_create()
    reset_test_user()
    ok = create_user(TEST_USERNAME, TEST_PASSWORD)
    assert ok, "Failed to create test user"


def check_generation_properties():
    codes = generate_backup_codes(n=10, length=10)
    assert len(codes) == 10, "Should generate exactly 10 codes"
    assert all(len(c) == 10 for c in codes), "Each code should be length 10"
    assert len(set(codes)) == len(codes), "Codes in small batch should be unique"


def check_store_and_remaining_count():
    setup_db_and_user()
    codes = generate_backup_codes(n=5, length=8)
    store_backup_codes(TEST_USERNAME, codes)
    count = remaining_backup_count(TEST_USERNAME)
    assert count == 5, f"Expected 5 remaining codes, got {count}"


def check_consume_once_only():
    setup_db_and_user()
    codes = generate_backup_codes(n=3, length=8)
    store_backup_codes(TEST_USERNAME, codes)

    first_code = codes[0]

    # First use should succeed
    ok1 = consume_backup_code(TEST_USERNAME, first_code)
    assert ok1 is True, "First use of valid backup code should succeed"
    count_after_first = remaining_backup_count(TEST_USERNAME)
    assert count_after_first == 2, f"Remaining codes should be 2, got {count_after_first}"

    # Second use should fail
    ok2 = consume_backup_code(TEST_USERNAME, first_code)
    assert ok2 is False, "Second use of same backup code should fail"
    count_after_second = remaining_backup_count(TEST_USERNAME)
    assert count_after_second == 2, "Remaining count should not change on failed consume"

    # Completely bogus code should also fail
    ok3 = consume_backup_code(TEST_USERNAME, "00000000")
    assert ok3 is False, "Random invalid backup code should fail"


def run_all():
    tests = [
        ("Backup codes generation properties", check_generation_properties),
        ("Store + remaining_count", check_store_and_remaining_count),
        ("Consume backup code once only", check_consume_once_only),
    ]

    print("=== Running backup code tests ===")
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except AssertionError as e:
            print(f"[FAIL] {name}: {e}")
        except Exception as e:
            print(f"[ERROR] {name}: unexpected exception: {e}")
    # Clean up after all tests
    reset_test_user()


if __name__ == "__main__":
    run_all()
