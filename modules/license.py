import hashlib
import random
import string
import datetime
from typing import Tuple

def generate_key(expiration_date: str) -> Tuple[str, str]:
    """
    Generates a license key with prefix PMI- and returns:
    (license_key, hashed_key)
    expiration_date format: YYYY-MM-DD
    """

    # Generate 16 random hex chars
    raw = ''.join(random.choices(string.hexdigits.upper(), k=16))

    # Format like PMI-XXXX-XXXX-XXXX-XXXX
    formatted = f"PMI-{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"

    # Hash key + expiration for secure validation
    to_hash = formatted + expiration_date
    hashed = hashlib.sha256(to_hash.encode()).hexdigest()

    return formatted, hashed


def validate_key(user_key: str, expiration_date: str, stored_hash: str) -> bool:
    """
    Validates a license key by hashing it with expiration date
    and comparing with stored hash.
    """

    today = datetime.date.today()
    exp = datetime.datetime.strptime(expiration_date, "%Y-%m-%d").date()

    if today > exp:
        return False  # expired

    to_hash = user_key + expiration_date
    hashed = hashlib.sha256(to_hash.encode()).hexdigest()

    return hashed == stored_hash
