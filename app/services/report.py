"""Tong hop so lieu bao cao tu bang transactions."""
from calendar import monthrange
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category, Transaction, TransactionType


def period_bounds(year: int | None, month: int | None):
    """Tra ve (tu_ngay, den_ngay). None nghia la khong gioi han."""
    if not year:
        return None, None
    if month:
        start = datetime(year, month, 1)
        last = monthrange(year, month)[1]
        end = datetime(year, month, last, 23, 59, 59)
    else:
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31, 23, 59, 59)
    return start, end


def _base_query(db: Session, user_id: int, start, end):
    q = db.query(Transaction).filter(Transaction.user_id == user_id)
    if start:
        q = q.filter(Transaction.date >= start)
    if end:
        q = q.filter(Transaction.date <= end)
    return q


def summary(db: Session, user_id: int, year=None, month=None) -> dict:
    """Tong thu, tong chi, so giao dich va so du trong ky."""
    start, end = period_bounds(year, month)

    rows = (
        _base_query(db, user_id, start, end)
        .with_entities(
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        )
        .group_by(Transaction.type)
        .all()
    )

    income = expense = 0
    count = 0
    for type_, total, n in rows:
        count += n
        if type_ == TransactionType.INCOME.value:
            income = int(total)
        else:
            expense = int(total)

    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "count": count,
    }


def by_category(db: Session, user_id: int, type_: str, year=None, month=None) -> list[dict]:
    """Ty trong theo tung danh muc, sap xep giam dan."""
    start, end = period_bounds(year, month)

    rows = (
        _base_query(db, user_id, start, end)
        .join(Category, Transaction.category_id == Category.id)
        .filter(Transaction.type == type_)
        .with_entities(Category.name, func.sum(Transaction.amount))
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    total = sum(int(t) for _, t in rows) or 1
    return [
        {"name": name, "amount": int(t), "percent": round(int(t) * 100 / total, 1)}
        for name, t in rows
    ]


def available_years(db: Session, user_id: int) -> list[int]:
    """Cac nam co phat sinh giao dich, moi nhat truoc."""
    rows = (
        db.query(func.strftime("%Y", Transaction.date))
        .filter(Transaction.user_id == user_id)
        .distinct()
        .all()
    )
    years = sorted({int(r[0]) for r in rows if r[0]}, reverse=True)
    return years or [datetime.now().year]