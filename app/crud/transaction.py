"""Truy van giao dich. Moi ham deu loc theo user_id."""
from sqlalchemy.orm import Session, joinedload

from app.models import Transaction
from app.schemas.transaction import TransactionCreate


def list_all(db: Session, user_id: int, limit: int = 200) -> list[Transaction]:
    """Danh sach giao dich cua mot tai khoan, moi nhat truoc."""
    return (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(limit)
        .all()
    )


def get(db: Session, tx_id: int, user_id: int) -> Transaction | None:
    """Lay mot giao dich. Tra ve None neu khong thuoc tai khoan nay."""
    return (
        db.query(Transaction)
        .filter(Transaction.id == tx_id, Transaction.user_id == user_id)
        .first()
    )


def create(db: Session, data: TransactionCreate, user_id: int) -> Transaction:
    obj = Transaction(
        amount=data.amount,
        type=data.type.value,
        date=data.date,
        note=data.note,
        category_id=data.category_id,
        user_id=user_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: Transaction, data: TransactionCreate) -> Transaction:
    obj.amount = data.amount
    obj.type = data.type.value
    obj.date = data.date
    obj.note = data.note
    obj.category_id = data.category_id
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: Transaction) -> None:
    db.delete(obj)
    db.commit()