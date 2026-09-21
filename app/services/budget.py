"""Tinh tinh trang ngan sach trong thang."""
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud import budget as crud_budget
from app.models import Transaction, TransactionType
from app.services.report import period_bounds

WARN_PERCENT = 80  # tu muc nay tro len thi canh bao


def _level(percent: float) -> str:
    if percent >= 100:
        return "over"
    if percent >= WARN_PERCENT:
        return "warning"
    return "ok"


def status(db: Session, user_id: int, year=None, month=None) -> list[dict]:
    """Moi ngan sach kem so da chi, phan tram va muc canh bao."""
    now = datetime.now()
    year, month = year or now.year, month or now.month
    start, end = period_bounds(year, month)

    rows = (
        db.query(Transaction.category_id, func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE.value,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .group_by(Transaction.category_id)
        .all()
    )
    spent_by_cat = {cid: int(total) for cid, total in rows}

    result = []
    for b in crud_budget.list_all(db, user_id):
        spent = spent_by_cat.get(b.category_id, 0)
        percent = round(spent * 100 / b.amount, 1)
        result.append({
            "budget": b,
            "name": b.category.name,
            "limit": b.amount,
            "spent": spent,
            "remaining": b.amount - spent,
            "percent": percent,
            "level": _level(percent),
        })
    result.sort(key=lambda r: r["percent"], reverse=True)
    return result


def alerts(db: Session, user_id: int) -> list[dict]:
    """Chi cac ngan sach dang o muc canh bao hoac da vuot."""
    return [r for r in status(db, user_id) if r["level"] != "ok"]