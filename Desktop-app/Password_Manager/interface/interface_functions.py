# interface/interface_functions.py
"""

Password generation & validation helpers & Password strength score

"""
import secrets  # this will generate random values
import string  # gives us access to strings

def validate_password(pwd: str):
    """
    checks if the password meets the following requirements:
    - minimum length of 16 characters
    - contains at least one uppercase letter
    - contains at least one lowercase letter
    - contains at least one symbol
    """
    missing = []  # list to store what requirements are missing
    if len(pwd) < 16:
        missing.append("length < 16")  # password is too short
    if not any(c.isupper() for c in pwd):
        missing.append("no uppercase letter")  # password missing uppercase
    if not any(c.islower() for c in pwd):
        missing.append("no lowercase letter")  # password missing lowercase
    if not any(c in string.punctuation for c in pwd):
        missing.append("no symbol")  # password missing symbol
    return (len(missing) == 0, missing)  # returns true if no missing elements else False
def password_strength_score(pwd: str) -> tuple[float, str]:
    """
    Evaluates password strength (0.0–99.9%) and aligns with validate_password() rules.
    To reach 99.9%, the password must:
      - Be at least 16 characters long
      - Contain uppercase, lowercase, digit, and symbol
      - Avoid excessive repetition
    """
    score = 0.0
    length = len(pwd)

    # Length contribution (0–40 points)
    if length >= 16:
        # full credit for long passwords, with small bonus for extra length
        score += 40.0 + min((length - 16) * 1.5, 10.0)
    elif length >= 12:
        score += 25.0
    elif length >= 8:
        score += 15.0
    else:
        score += length * 1.0  # small credit for short passwords

    # Character diversity (0–50 points)
    has_lower = any(c.islower() for c in pwd)
    has_upper = any(c.isupper() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    has_symbol = any(c in string.punctuation for c in pwd)

    # assign base points for each requirement
    diversity_points = 0.0
    if has_lower:
        diversity_points += 10.0
    if has_upper:
        diversity_points += 10.0
    if has_digit:
        diversity_points += 10.0
    if has_symbol:
        diversity_points += 15.0

    score += diversity_points

    # Variety / uniqueness (0–10 points)
    unique_chars = len(set(pwd))
    if unique_chars > 10:
        score += 10.0
    elif unique_chars > 6:
        score += 5.0

    #  Penalty for repetition
    if len(set(pwd)) < len(pwd) * 0.4:
        score *= 0.8  # too repetitive

    # Cap and normalize
    score = min(round(score, 1), 99.9)

    # Label
    if score < 40:
        label = "Weak"
    elif score < 70:
        label = "Medium"
    else:
        label = "Strong"

    return score, label


def generate_password(length: int = 16) -> str:  # function starts at a minimum of 16 characters and will return a string
    """
    requirements for a strong password are as followed

    one lowercase letter
    one uppercase letter
    one digit
    one symbol
    minimum length is 16 characters

    """
    try:
        length = int(length)  # tries to turn length into an integer
    except Exception:
        length = 16  # if it fails it will default to 16
    length = max(16, length)  # if the user sets something less than 16, set it to 16

    lowers = string.ascii_lowercase  # lowercase letters a–z
    uppers = string.ascii_uppercase  # uppercase letters A–Z
    digits = string.digits           # digits 0–9
    symbols = string.punctuation     # symbols

    # will require that one character from each category is pulled for the password
    required = [
        secrets.choice(lowers),   # 1 random lowercase letter
        secrets.choice(uppers),   # 1 random uppercase letter
        secrets.choice(digits),   # 1 random digit
        secrets.choice(symbols),  # 1 random special character
    ]

    all_chars = lowers + uppers + digits + symbols  # combines all character sets
    remaining = [secrets.choice(all_chars) for _ in range(length - len(required))]  # remaining characters are randomly chosen from all sets

    pwd_list = required + remaining  # merges both the requirements and the remaining characters together
    for i in range(len(pwd_list) - 1, 0, -1):  # goes backwards through the list of characters
        j = secrets.randbelow(i + 1)  # gets a random index in the list
        pwd_list[i], pwd_list[j] = pwd_list[j], pwd_list[i]  # swaps characters to shuffle the password list

    return "".join(pwd_list)  # joins the whole list into a single string and returns the string