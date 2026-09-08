from pydantic import BaseModel, ConfigDict, field_validator

from app.models import TransactionType


class CategoryCreate(BaseModel):
    """Du lieu tao moi hoac cap nhat danh muc."""
    name: str
    description: str | None = None
    type: TransactionType

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Ten danh muc phai co it nhat 2 ky tu")
        if len(v) > 100:
            raise ValueError("Ten danh muc khong duoc qua 100 ky tu")
        return v

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = " ".join(v.split())
        return v or None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    type: str