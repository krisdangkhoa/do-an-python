"""Quan ly danh mục thu - chi."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import category as crud_category
from app.database import get_db
from app.deps import get_current_user
from app.models import TransactionType, User
from app.schemas.category import CategoryCreate
from app.templating import templates

router = APIRouter(prefix="/categories", tags=["categories"])


def _page(request: Request, db: Session, user: User, **extra):
    """Dung du lieu chung cho trang danh muc."""
    ctx = {
        "request": request,
        "user": user,
        "categories": crud_category.list_all(db, user.id),
        "types": list(TransactionType),
        "active": "categories",
    }
    ctx.update(extra)
    return ctx


@router.get("")
def index(
    request: Request,
    edit: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Neu co ?edit=<id> thi nap san danh muc do vao bieu mau.
    # crud.get da loc theo user_id nen khong sua duoc danh muc cua nguoi khac.
    editing = crud_category.get(db, edit, user.id) if edit else None
    return templates.TemplateResponse(
        "category.html", _page(request, db, user, editing=editing)
    )


@router.post("")
def create(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    type: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    form = {"name": name, "description": description, "type": type}

    def fail(msg: str):
        return templates.TemplateResponse(
            "category.html",
            _page(request, db, user, error=msg, form=form),
            status_code=400,
        )

    try:
        data = CategoryCreate(name=name, description=description, type=type)
    except ValidationError as exc:
        return fail(exc.errors()[0]["msg"])

    if crud_category.name_exists(db, data.name, user.id):
        return fail(f"Danh mục “{data.name}” đã tồn tại trong tài khoản của bạn.")

    crud_category.create(db, data, user.id)
    return RedirectResponse("/categories?ok=created", status_code=303)


@router.post("/{category_id}/edit")
def edit_post(
    category_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    type: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_category.get(db, category_id, user.id)
    if obj is None:
        # Khong ton tai HOAC khong thuoc tai khoan nay - deu bao khong tim thay
        return RedirectResponse("/categories?err=notfound", status_code=303)

    def fail(msg: str):
        return templates.TemplateResponse(
            "category.html",
            _page(request, db, user, error=msg, editing=obj),
            status_code=400,
        )

    try:
        data = CategoryCreate(name=name, description=description, type=type)
    except ValidationError as exc:
        return fail(exc.errors()[0]["msg"])

    if crud_category.name_exists(db, data.name, user.id, exclude_id=obj.id):
        return fail(f"Danh mục “{data.name}” đã tồn tại trong tài khoản của bạn.")

    crud_category.update(db, obj, data)
    return RedirectResponse("/categories?ok=updated", status_code=303)


@router.post("/{category_id}/delete")
def delete(
    category_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = crud_category.get(db, category_id, user.id)
    if obj is None:
        return RedirectResponse("/categories?err=notfound", status_code=303)

    if crud_category.usage_count(db, obj.id) > 0:
        return RedirectResponse("/categories?err=inuse", status_code=303)

    crud_category.delete(db, obj)
    return RedirectResponse("/categories?ok=deleted", status_code=303)