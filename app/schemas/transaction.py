from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import TransactionType

MAX_AMOUNT = 999_999_999_999  # gioi han de tranh nhap nham


class TransactionCreate(BaseModel):
    """Du lieu tao moi hoac cap nhat giao dich."""
    amount: int
    type: TransactionType
    date: datetime
    note: str | None = None
    category_id: int

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, v):
        # Chap nhan chuoi co dau cham hoac dau phay: 1.200.000
        if isinstance(v, str):
            v = v.strip().replace(".", "").replace(",", "").replace(" ", "")
            if not v:
                raise ValueError("Vui long nhap so tien")
            try:
                v = int(v)
            except ValueError:
                raise ValueError("So tien phai la mot so nguyen")
        return v

    @field_validator("amount")
    @classmethod
    def check_amount(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("So tien phai lon hon 0")
        if v > MAX_AMOUNT:
            raise ValueError("So tien vuot qua gioi han cho phep")
        return v

    @field_validator("note")
    @classmethod
    def check_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = " ".join(v.split())
        if len(v) > 255:
            raise ValueError("Ghi chu khong duoc qua 255 ky tu")
        return v or None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: int
    type: str
    date: datetime
    note: str | None
    category_id: int