"""Phu thuoc dung chung: session database va nguoi dung dang dang nhap."""
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


class NotAuthenticated(Exception):
    """Nem ra khi chua dang nhap, main.py se chuyen huong ve /login."""


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise NotAuthenticated()

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise NotAuthenticated()
    return user