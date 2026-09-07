import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserCreate(BaseModel):
    """Du lieu dang ky tai khoan moi."""
    username: str
    email: str
    full_name: str
    password: str

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Ten dang nhap phai co it nhat 3 ky tu")
        if not re.fullmatch(r"[A-Za-z0-9_.]+", v):
            raise ValueError("Ten dang nhap chi gom chu, so, dau gach duoi va dau cham")
        return v

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Dia chi email khong hop le")
        return v

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Ho ten khong duoc de trong")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Mat khau phai co it nhat 6 ky tu")
        return v


class UserOut(BaseModel):
    """Du lieu tra ve - khong bao gio chua hashed_password."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str
    created_at: datetime