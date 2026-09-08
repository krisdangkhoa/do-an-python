"""Truy van danh muc. Moi ham deu loc theo user_id."""
from sqlalchemy.orm import Session

from app.models import Category, Reminder, Transaction
from app.schemas.category import CategoryCreate


def list_all(db: Session, user_id: int, type_: str | None = None) -> list[Category]:
    """Danh sach danh muc cua mot tai khoan, co the loc theo loai."""
    q = db.query(Category).filter(Category.user_id == user_id)
    if type_:
        q = q.filter(Category.type == type_)
    return q.order_by(Category.type, Category.name).all()


def get(db: Session, category_id: int, user_id: int) -> Category | None:
    """Lay mot danh muc. Tra ve None neu khong thuoc tai khoan nay."""
    return (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user_id)
        .first()
    )


def name_exists(db: Session, name: str, user_id: int, exclude_id: int | None = None) -> bool:
    """Kiem tra trung ten trong pham vi mot tai khoan."""
    q = db.query(Category).filter(
        Category.user_id == user_id,
        Category.name == name,
    )
    if exclude_id is not None:
        q = q.filter(Category.id != exclude_id)
    return db.query(q.exists()).scalar()


def create(db: Session, data: CategoryCreate, user_id: int) -> Category:
    obj = Category(
        name=data.name,
        description=data.description,
        type=data.type.value,
        user_id=user_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: Category, data: CategoryCreate) -> Category:
    obj.name = data.name
    obj.description = data.description
    obj.type = data.type.value
    db.commit()
    db.refresh(obj)
    return obj


def usage_count(db: Session, category_id: int) -> int:
    """Dem so giao dich va loi nhac dang dung danh muc nay."""
    tx = db.query(Transaction).filter(Transaction.category_id == category_id).count()
    rm = db.query(Reminder).filter(Reminder.category_id == category_id).count()
    return tx + rm


def delete(db: Session, obj: Category) -> None:
    db.delete(obj)
    db.commit()