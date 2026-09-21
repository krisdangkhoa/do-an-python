"""Quan ly ngan sach theo danh muc."""
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import budget as crud_budget
from app.crud import category as crud_category
from app.database import get_db
from app.deps import get_current_user
from app.models import TransactionType, User
from app.schemas.budget import BudgetCreate
from app.services import budget as svc
from app.templating import templates

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _page(request: Request, db: Session, user: User, **extra):
    now = datetime.now()
    ctx = {
        "request": request,
        "user": user,
        "active": "budgets",
        "rows": svc.status(db, user.id),
        "categories": crud_category.list_all(db, user.id, TransactionType.EXPENSE.value),
        "month_label": f"Tháng {now.month}/{now.year}",
    }
    ctx.update(extra)
    return ctx


def _validate(db: Session, user: User, category_id, amount):
    try:
        cat_id = int(category_id)
    except (ValueError, TypeError):
        return None, "Vui lòng chọn danh mục."
    cat = crud_category.get(db, cat_id, user.id)
    if cat is None:
        return None, "Danh mục không hợp lệ."
    if cat.type != TransactionType.EXPENSE.value:
        return None, "Chỉ đặt ngân sách cho danh mục chi tiêu."
    try:
        data = BudgetCreate(category_id=cat_id, amount=amount)
    except ValidationError as exc:
        return None, exc.errors()[0]["msg"]
    return data, None


@router.get("")
def index(
    request: Request,
    edit: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    editing = crud_budget.get(db, edit, user.id) if edit else None
    return templates.TemplateResponse("budget.html", _page(request, db, user, editing=editing))


@router.post("")
def create(
    request: Request,
    category_id: str = Form(...),
    amount: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data, err = _validate(db, user, category_id, amount)
    if not err and crud_budget.get_by_category(db, data.category_id, user.id):
        err = "Danh mục này đã có ngân sách, hãy bấm Sửa để đổi hạn mức."
    if err:
        return templates.TemplateResponse(
            "budget.html", _page(request, db, user, error=err), status_code=400
        )
    crud_budget.create(db, data.category_id, data.amount, user.id)
    return RedirectResponse("/budgets?ok=created", status_code=303)


@router.post("/{budget_id}/edit")
def edit_post(
    budget_id: int,
    request: Request,
    amount: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_budget.get(db, budget_id, user.id)
    if obj is None:
        return RedirectResponse("/budgets?err=notfound", status_code=303)
    data, err = _validate(db, user, obj.category_id, amount)
    if err:
        return templates.TemplateResponse(
            "budget.html", _page(request, db, user, error=err, editing=obj), status_code=400
        )
    crud_budget.update(db, obj, data.amount)
    return RedirectResponse("/budgets?ok=updated", status_code=303)


@router.post("/{budget_id}/delete")
def delete(
    budget_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_budget.get(db, budget_id, user.id)
    if obj is None:
        return RedirectResponse("/budgets?err=notfound", status_code=303)
    crud_budget.delete(db, obj)
    return RedirectResponse("/budgets?ok=deleted", status_code=303)