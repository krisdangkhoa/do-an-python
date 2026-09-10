from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import RepeatType, TransactionType
from app.schemas.transaction import MAX_AMOUNT


class ReminderCreate(BaseModel):
    """Du lieu tao moi hoac cap nhat loi nhac."""
    message: str
    amount: int
    type: TransactionType
    remind_time: datetime
    repeat_type: RepeatType
    active: bool = True
    auto_add_transaction: bool = False
    category_id: int

    @field_validator("message")
    @classmethod
    def check_message(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Noi dung nhac phai co it nhat 2 ky tu")
        if len(v) > 255:
            raise ValueError("Noi dung nhac khong duoc qua 255 ky tu")
        return v

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, v):
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


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    amount: int
    type: str
    remind_time: datetime
    repeat_type: str
    active: bool
    auto_add_transaction: bool
    category_id: int