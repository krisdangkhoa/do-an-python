"""Quan ly loi nhac dinh ky."""
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import category as crud_category
from app.crud import reminder as crud_reminder
from app.database import get_db
from app.deps import get_current_user
from app.models import RepeatType, TransactionType, User
from app.schemas.reminder import ReminderCreate
from app.templating import templates

router = APIRouter(prefix="/reminders", tags=["reminders"])

REPEAT_LABELS = {
    "none": "Không lặp",
    "daily": "Hằng ngày",
    "weekly": "Hằng tuần",
    "monthly": "Hằng tháng",
}


def _page(request: Request, db: Session, user: User, **extra):
    ctx = {
        "request": request,
        "user": user,
        "reminders": crud_reminder.list_all(db, user.id),
        "categories": crud_category.list_all(db, user.id),
        "types": list(TransactionType),
        "repeats": list(RepeatType),
        "repeat_labels": REPEAT_LABELS,
        "now": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "active": "reminders",
    }
    ctx.update(extra)
    return ctx


def _validate(db, user, message, amount, type_, remind_time, repeat_type,
              active, auto_add, category_id):
    try:
        dt = datetime.fromisoformat(remind_time)
    except (ValueError, TypeError):
        return None, "Thời gian nhắc không hợp lệ."

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
        data = ReminderCreate(
            message=message, amount=amount, type=type_,
            remind_time=dt, repeat_type=repeat_type,
            active=active, auto_add_transaction=auto_add,
            category_id=cat_id,
        )
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
    editing = crud_reminder.get(db, edit, user.id) if edit else None
    return templates.TemplateResponse(
        "reminder.html", _page(request, db, user, editing=editing)
    )


@router.post("")
def create(
    request: Request,
    message: str = Form(...),
    amount: str = Form(...),
    type: str = Form(...),
    remind_time: str = Form(...),
    repeat_type: str = Form("none"),
    active: str = Form(None),
    auto_add_transaction: str = Form(None),
    category_id: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data, err = _validate(
        db, user, message, amount, type, remind_time, repeat_type,
        active is not None, auto_add_transaction is not None, category_id,
    )
    if err:
        return templates.TemplateResponse(
            "reminder.html", _page(request, db, user, error=err), status_code=400
        )

    crud_reminder.create(db, data, user.id)
    return RedirectResponse("/reminders?ok=created", status_code=303)


@router.post("/{reminder_id}/edit")
def edit_post(
    reminder_id: int,
    request: Request,
    message: str = Form(...),
    amount: str = Form(...),
    type: str = Form(...),
    remind_time: str = Form(...),
    repeat_type: str = Form("none"),
    active: str = Form(None),
    auto_add_transaction: str = Form(None),
    category_id: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_reminder.get(db, reminder_id, user.id)
    if obj is None:
        return RedirectResponse("/reminders?err=notfound", status_code=303)

    data, err = _validate(
        db, user, message, amount, type, remind_time, repeat_type,
        active is not None, auto_add_transaction is not None, category_id,
    )
    if err:
        return templates.TemplateResponse(
            "reminder.html",
            _page(request, db, user, error=err, editing=obj),
            status_code=400,
        )

    crud_reminder.update(db, obj, data)
    return RedirectResponse("/reminders?ok=updated", status_code=303)


@router.post("/{reminder_id}/toggle")
def toggle(
    reminder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_reminder.get(db, reminder_id, user.id)
    if obj is None:
        return RedirectResponse("/reminders?err=notfound", status_code=303)
    crud_reminder.toggle(db, obj)
    return RedirectResponse("/reminders?ok=toggled", status_code=303)


@router.post("/{reminder_id}/delete")
def delete(
    reminder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_reminder.get(db, reminder_id, user.id)
    if obj is None:
        return RedirectResponse("/reminders?err=notfound", status_code=303)
    crud_reminder.delete(db, obj)
    return RedirectResponse("/reminders?ok=deleted", status_code=303)