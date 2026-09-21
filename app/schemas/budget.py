from pydantic import BaseModel, field_validator

from app.schemas.transaction import MAX_AMOUNT


class BudgetCreate(BaseModel):
    """Han muc chi tieu hang thang."""
    category_id: int
    amount: int

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, v):
        if isinstance(v, str):
            v = v.strip().replace(".", "").replace(",", "").replace(" ", "")
            if not v:
                raise ValueError("Vui long nhap han muc")
            try:
                v = int(v)
            except ValueError:
                raise ValueError("Han muc phai la mot so nguyen")
        return v

    @field_validator("amount")
    @classmethod
    def check_amount(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Han muc phai lon hon 0")
        if v > MAX_AMOUNT:
            raise ValueError("Han muc vuot qua gioi han cho phep")
        return v