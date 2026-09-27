"""Sau moi khoan chi, kiem tra ngan sach va quyet dinh co gui canh bao."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.crud import budget as crud_budget
from app.models import BudgetAlert, TransactionType
from app.services import budget as svc_budget
from app.services.mailer import LEVEL_TEXT, _vnd


def check(db: Session, user_id: int, category_id: int, when: datetime, type_: str) -> dict | None:
    """Tra ve thong tin canh bao neu vua cham muc moi, nguoc lai tra ve None."""
    if type_ != TransactionType.EXPENSE.value:
        return None
    budget = crud_budget.get_by_category(db, category_id, user_id)
    if budget is None:
        return None

    rows = svc_budget.status(db, user_id, when.year, when.month)
    row = next((r for r in rows if r["budget"].id == budget.id), None)
    if row is None or row["level"] == "ok":
        return None

    month = when.strftime("%Y-%m")
    already = (
        db.query(BudgetAlert)
        .filter_by(budget_id=budget.id, month=month, level=row["level"])
        .first()
    )
    if already:
        return None  # muc nay da gui trong thang, khong gui lai

    db.add(BudgetAlert(budget_id=budget.id, user_id=user_id, month=month, level=row["level"]))
    db.commit()
    return {
        "name": row["name"], "limit": row["limit"], "spent": row["spent"],
        "remaining": row["remaining"], "percent": row["percent"],
        "level": row["level"], "month": f"{when.month}/{when.year}",
    }


def message(alert: dict) -> str:
    return (
        f"Ngân sách {alert['name']} {LEVEL_TEXT[alert['level']]}: "
        f"đã chi {_vnd(alert['spent'])} / {_vnd(alert['limit'])} ({alert['percent']}%)."
    )