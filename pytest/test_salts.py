
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.encryption import _random_salt, _hash_pw_with_salt

def check_random_salt_properties():
    # salt is bytes and has default length 16
    salt = _random_salt()
    assert isinstance(salt, bytes), "Salt should be bytes"
    assert len(salt) == 16, "Default salt length should be 16 bytes"

    # two salts should almost never be equal
    salt2 = _random_salt()
    assert salt != salt2, "Two generated salts should not be identical"


def check_hash_deterministic_for_same_salt():
    password = "StrongTestPass!123"
    salt = _random_salt()

    h1 = _hash_pw_with_salt(password, salt)
    h2 = _hash_pw_with_salt(password, salt)

    assert isinstance(h1, str), "Hashed password should be a string"
    assert h1 == h2, "Same password + same salt must give same hash"


def check_hash_changes_with_salt():
    password = "StrongTestPass!123"
    salt1 = _random_salt()
    salt2 = _random_salt()

    h1 = _hash_pw_with_salt(password, salt1)
    h2 = _hash_pw_with_salt(password, salt2)

    assert h1 != h2, "Same password with different salts should give different hashes"


def run_all():
    tests = [
        ("Salt basic properties", check_random_salt_properties),
        ("Hash deterministic per salt", check_hash_deterministic_for_same_salt),
        ("Hash changes with salt", check_hash_changes_with_salt),
    ]

    print("=== Running salt / hash tests ===")
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except AssertionError as e:
            print(f"[FAIL] {name}: {e}")
        except Exception as e:
            print(f"[ERROR] {name}: unexpected exception: {e}")


if __name__ == "__main__":
    run_all()
