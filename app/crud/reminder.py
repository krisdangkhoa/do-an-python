"""Truy van loi nhac. Moi ham deu loc theo user_id."""
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models import Reminder
from app.schemas.reminder import ReminderCreate


def list_all(db: Session, user_id: int) -> list[Reminder]:
    return (
        db.query(Reminder)
        .options(joinedload(Reminder.category))
        .filter(Reminder.user_id == user_id)
        .order_by(Reminder.remind_time.asc())
        .all()
    )


def get(db: Session, reminder_id: int, user_id: int) -> Reminder | None:
    return (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id, Reminder.user_id == user_id)
        .first()
    )


def create(db: Session, data: ReminderCreate, user_id: int) -> Reminder:
    obj = Reminder(
        message=data.message,
        amount=data.amount,
        type=data.type.value,
        remind_time=data.remind_time,
        repeat_type=data.repeat_type.value,
        active=data.active,
        auto_add_transaction=data.auto_add_transaction,
        category_id=data.category_id,
        user_id=user_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: Reminder, data: ReminderCreate) -> Reminder:
    obj.message = data.message
    obj.amount = data.amount
    obj.type = data.type.value
    obj.remind_time = data.remind_time
    obj.repeat_type = data.repeat_type.value
    obj.active = data.active
    obj.auto_add_transaction = data.auto_add_transaction
    obj.category_id = data.category_id
    db.commit()
    db.refresh(obj)
    return obj


def toggle(db: Session, obj: Reminder) -> Reminder:
    """Bat hoac tat mot loi nhac ma khong xoa."""
    obj.active = not obj.active
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: Reminder) -> None:
    db.delete(obj)
    db.commit()


def due_reminders(db: Session, now: datetime) -> list[Reminder]:
    """Cac loi nhac dang bat va da den han. Dung cho scheduler."""
    return (
        db.query(Reminder)
        .filter(Reminder.active.is_(True), Reminder.remind_time <= now)
        .all()
    )