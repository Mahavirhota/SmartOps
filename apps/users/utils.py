import secrets
import string


def generate_random_password(length=12):
    """
    Generate a secure random password with at least one lowercase,
    one uppercase, one digit, and one special character.
    """
    if length < 8:
        length = 8

    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in string.punctuation for c in password)):
            return password
