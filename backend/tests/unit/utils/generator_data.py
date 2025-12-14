import secrets
import string

from faker import Faker

fake = Faker()


def generate_email():
    return fake.email()


def generate_password(length=None):
    if length is None:
        return fake.password()
    return fake.password(length)


def generate_token(length: int = 100) -> str:
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))