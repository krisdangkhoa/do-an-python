"""Trang chu va trang bao cao thong ke."""
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import TransactionType, User
from app.services import report as svc
from app.templating import templates

router = APIRouter(tags=["report"])

MONTHS = [(i, f"Tháng {i}") for i in range(1, 13)]


def _filters(db: Session, user: User, year, month):
    """Chuan hoa tham so loc va du lieu cho hai o chon."""
    now = datetime.now()
    years = svc.available_years(db, user.id)
    y = year if year in years else (now.year if now.year in years else years[0])
    m = month if month in range(1, 13) else None
    return y, m, years


@router.get("/")
def home(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    y, m, years = _filters(db, user, year, month)
    data = svc.summary(db, user.id, y, m)
    return templates.TemplateResponse("home.html", {
        "request": request, "user": user, "active": "home",
        "s": data, "year": y, "month": m,
        "years": years, "months": MONTHS,
    })


@router.get("/report")
def report(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    y, m, years = _filters(db, user, year, month)
    return templates.TemplateResponse("report.html", {
        "request": request, "user": user, "active": "report",
        "s": svc.summary(db, user.id, y, m),
        "expense_rows": svc.by_category(db, user.id, TransactionType.EXPENSE.value, y, m),
        "income_rows": svc.by_category(db, user.id, TransactionType.INCOME.value, y, m),
        "year": y, "month": m, "years": years, "months": MONTHS,
    })