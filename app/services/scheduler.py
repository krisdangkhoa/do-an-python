"""Chay nen: kiem tra loi nhac den han va tu sinh giao dich."""
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.crud import reminder as crud_reminder
from app.database import SessionLocal
from app.models import RepeatType, Transaction

log = logging.getLogger("scheduler")

CHECK_INTERVAL_SECONDS = 60


def _next_time(current: datetime, repeat: str) -> datetime | None:
    """Tinh moc nhac ke tiep. Tra ve None neu khong lap lai."""
    if repeat == RepeatType.DAILY.value:
        return current + timedelta(days=1)
    if repeat == RepeatType.WEEKLY.value:
        return current + timedelta(weeks=1)
    if repeat == RepeatType.MONTHLY.value:
        # Cong them mot thang, giu nguyen ngay neu co the
        year, month = current.year, current.month + 1
        if month > 12:
            year, month = year + 1, 1
        day = current.day
        while day > 0:
            try:
                return current.replace(year=year, month=month, day=day)
            except ValueError:
                day -= 1  # thang ngan hon, lui dan (31 -> 30 -> 29 -> 28)
    return None


def process_due_reminders() -> int:
    """Xu ly cac loi nhac den han. Tra ve so loi nhac da xu ly."""
    db = SessionLocal()
    processed = 0
    try:
        now = datetime.now()
        for rm in crud_reminder.due_reminders(db, now):
            if rm.auto_add_transaction:
                db.add(Transaction(
                    amount=rm.amount,
                    type=rm.type,
                    date=rm.remind_time,
                    note=f"[Tự động] {rm.message}",
                    category_id=rm.category_id,
                    user_id=rm.user_id,
                ))

            nxt = _next_time(rm.remind_time, rm.repeat_type)
            if nxt:
                rm.remind_time = nxt
            else:
                rm.active = False  # khong lap lai thi tat sau khi chay

            processed += 1

        if processed:
            db.commit()
            log.info("Da xu ly %d loi nhac den han", processed)
    except Exception:
        db.rollback()
        log.exception("Loi khi xu ly loi nhac")
    finally:
        db.close()
    return processed


scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")


def start():
    if scheduler.running:
        return
    scheduler.add_job(
        process_due_reminders,
        "interval",
        seconds=CHECK_INTERVAL_SECONDS,
        id="due_reminders",
        replace_existing=True,
    )
    scheduler.start()
    log.info("Scheduler da khoi dong, kiem tra moi %d giay", CHECK_INTERVAL_SECONDS)


def shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)