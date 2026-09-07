"""Bam va kiem tra mat khau bang bcrypt."""
import bcrypt

MAX_BYTES = 72  # gioi han cua thuat toan bcrypt


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:MAX_BYTES]


def hash_password(password: str) -> str:
    """Bam mat khau kem salt ngau nhien."""
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """So sanh mat khau nhap vao voi gia tri da bam."""
    try:
        return bcrypt.checkpw(_encode(plain), hashed.encode("utf-8"))
    except ValueError:
        return False