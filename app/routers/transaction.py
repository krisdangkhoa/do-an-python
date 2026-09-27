"""Quan ly giao dich thu - chi."""
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import category as crud_category
from app.crud import transaction as crud_tx
from app.database import get_db
from app.deps import get_current_user
from app.models import Transaction, TransactionType, User
from app.schemas.transaction import TransactionCreate
from app.services import budget_alert, mailer
from app.templating import templates

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _page(request: Request, db: Session, user: User, **extra):
    ctx = {
        "request": request,
        "user": user,
        "transactions": crud_tx.list_all(db, user.id),
        "categories": crud_category.list_all(db, user.id),
        "types": list(TransactionType),
        "now": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "active": "transactions",
    }
    ctx.update(extra)
    return ctx


def _validate(db: Session, user: User, amount, type_, date_, note, category_id):
    """Kiem tra du lieu. Tra ve (data, loi). Mot trong hai luon la None."""
    try:
        dt = datetime.fromisoformat(date_)
    except (ValueError, TypeError):
        return None, "Ngày giờ không hợp lệ."

    try:
        cat_id = int(category_id)
    except (ValueError, TypeError):
        return None, "Vui lòng chọn danh mục."

    cat = crud_category.get(db, cat_id, user.id)
    if cat is None:
        return None, "Danh mục không hợp lệ."

    if cat.type != type_:
        loai = "thu nhập" if type_ == "income" else "chi tiêu"
        return None, f"Danh mục “{cat.name}” không thuộc loại {loai}."

    try:
        data = TransactionCreate(
            amount=amount, type=type_, date=dt,
            note=note, category_id=cat_id,
        )
    except ValidationError as exc:
        return None, exc.errors()[0]["msg"]

    return data, None


def _check_budget(request: Request, background: BackgroundTasks, db: Session,
                  user: User, tx: Transaction) -> None:
    """Neu khoan chi vua lam cham muc canh bao: gui email chay nen va bao tren man hinh."""
    alert = budget_alert.check(db, user.id, tx.category_id, tx.date, tx.type)
    if alert:
        background.add_task(mailer.send_budget_alert, user.email, user.full_name, alert)
        request.session["flash"] = f"{budget_alert.message(alert)} Đã gửi email cảnh báo tới {user.email}."


@router.get("")
def index(
    request: Request,
    edit: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    editing = crud_tx.get(db, edit, user.id) if edit else None
    return templates.TemplateResponse(
        "transaction.html", _page(request, db, user, editing=editing)
    )


@router.post("")
def create(
    request: Request,
    background: BackgroundTasks,
    amount: str = Form(...),
    type: str = Form(...),
    date: str = Form(...),
    note: str = Form(""),
    category_id: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data, err = _validate(db, user, amount, type, date, note, category_id)
    if err:
        form = {"amount": amount, "type": type, "date": date,
                "note": note, "category_id": category_id}
        return templates.TemplateResponse(
            "transaction.html",
            _page(request, db, user, error=err, form=form),
            status_code=400,
        )

    tx = crud_tx.create(db, data, user.id)
    _check_budget(request, background, db, user, tx)
    return RedirectResponse("/transactions?ok=created", status_code=303)


@router.post("/{tx_id}/edit")
def edit_post(
    tx_id: int,
    request: Request,
    background: BackgroundTasks,
    amount: str = Form(...),
    type: str = Form(...),
    date: str = Form(...),
    note: str = Form(""),
    category_id: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_tx.get(db, tx_id, user.id)
    if obj is None:
        return RedirectResponse("/transactions?err=notfound", status_code=303)

    data, err = _validate(db, user, amount, type, date, note, category_id)
    if err:
        return templates.TemplateResponse(
            "transaction.html",
            _page(request, db, user, error=err, editing=obj),
            status_code=400,
        )

    tx = crud_tx.update(db, obj, data)
    _check_budget(request, background, db, user, tx)
    return RedirectResponse("/transactions?ok=updated", status_code=303)


@router.post("/{tx_id}/delete")
def delete(
    tx_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_tx.get(db, tx_id, user.id)
    if obj is None:
        return RedirectResponse("/transactions?err=notfound", status_code=303)

    crud_tx.delete(db, obj)
    return RedirectResponse("/transactions?ok=deleted", status_code=303)