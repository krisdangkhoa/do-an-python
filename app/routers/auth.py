"""Dang ky, dang nhap, dang xuat."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import user as crud_user
from app.database import get_db
from app.schemas.user import UserCreate
from app.templating import templates

router = APIRouter(tags=["auth"])


@router.get("/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = crud_user.authenticate(db, username.strip(), password)
    if user is None:
        # Thong bao chung chung, khong tiet lo ten dang nhap nao ton tai
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Tên đăng nhập hoặc mật khẩu không đúng.",
             "username": username},
            status_code=400,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.get("/register")
def register_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    db: Session = Depends(get_db),
):
    form = {"username": username, "email": email, "full_name": full_name}

    def fail(message: str):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": message, **form},
            status_code=400,
        )

    if password != password2:
        return fail("Hai lần nhập mật khẩu không khớp nhau.")

    try:
        data = UserCreate(
            username=username, email=email,
            full_name=full_name, password=password,
        )
    except ValidationError as exc:
        return fail(exc.errors()[0]["msg"])

    if crud_user.get_by_username(db, data.username):
        return fail("Tên đăng nhập này đã được sử dụng.")
    if crud_user.get_by_email(db, data.email):
        return fail("Địa chỉ email này đã được đăng ký.")

    crud_user.create(db, data)
    return RedirectResponse("/login?created=1", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)