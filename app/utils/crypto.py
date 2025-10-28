import os
import base64

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

SALT_SIZE = 16
KDF_ITERATIONS = 390_000


def _derive_key(
    passphrase: str, salt: bytes, iterations: int = KDF_ITERATIONS
) -> bytes:
    """
    Derive a 32-byte key suitable for Fernet from a passphrase and salt.
    Returns the URL-safe base64-encoded key bytes (as required by Fernet).
    """
    if isinstance(passphrase, str):
        passphrase_bytes = passphrase.encode("utf-8")
    else:
        passphrase_bytes = passphrase
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    key = kdf.derive(passphrase_bytes)
    return base64.urlsafe_b64encode(key)


def generate_salt() -> bytes:
    return os.urandom(SALT_SIZE)


def encrypt_file(in_path: str, out_path: str, passphrase: str) -> None:
    """
    Encrypt file at in_path into out_path.
    File format: <salt (16 bytes)><Fernet token bytes>
    """
    salt = generate_salt()
    key = _derive_key(passphrase, salt)
    f = Fernet(key)

    with open(in_path, "rb") as f_in:
        plaintext = f_in.read()

    token = f.encrypt(plaintext)

    with open(out_path, "wb") as f_out:
        f_out.write(salt)
        f_out.write(token)


def decrypt_file(in_path: str, out_path: str, passphrase: str) -> None:
    """
    Decrypt a file previously encrypted with encrypt_file.
    Expects first SALT_SIZE bytes to be salt; remainder is Fernet token.
    """
    with open(in_path, "rb") as f_in:
        data = f_in.read()
    if len(data) < SALT_SIZE:
        raise ValueError("Input file is too short (no salt found).")
    salt = data[:SALT_SIZE]
    token = data[SALT_SIZE:]
    key = _derive_key(passphrase, salt)
    f = Fernet(key)
    plaintext = f.decrypt(token)
    with open(out_path, "wb") as f_out:
        f_out.write(plaintext)


def is_encrypted_file(path: str) -> bool:
    """
    Heuristic: check file size and salt presence. If file is at least SALT_SIZE bytes -> True.
    This is only a minor helper; in production you may want a file header/magic.
    """
    try:
        size = os.path.getsize(path)
        return size > SALT_SIZE
    except Exception:
        return False
