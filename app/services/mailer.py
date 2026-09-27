"""Gui email. Neu chua cau hinh SMTP thi in noi dung ra man hinh (che do thu)."""
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

log = logging.getLogger("mailer")

LEVEL_TEXT = {"warning": "sắp chạm hạn mức", "over": "đã vượt hạn mức"}


def _vnd(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def is_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _print(to: str, subject: str, body: str, reason: str) -> None:
    line = "=" * 64
    print(f"\n{line}\n[EMAIL - {reason}]\nĐến: {to}\nTiêu đề: {subject}\n\n{body}\n{line}\n", flush=True)


def deliver(to: str, subject: str, body: str) -> bool:
    """Gui that qua SMTP. Tra ve True neu gui duoc."""
    if not is_configured():
        _print(to, subject, body, "chế độ thử, chưa cấu hình SMTP")
        return False
    msg = EmailMessage()
    msg["From"] = settings.MAIL_FROM or settings.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        log.info("Da gui email toi %s", to)
        return True
    except Exception as exc:
        log.exception("Gui email that bai")
        _print(to, subject, body, f"gửi thất bại: {exc}")
        return False


# Cac noi khac goi ham nay. Khi kiem thu se thay bang ham gia.
send_email = deliver


def send_budget_alert(to: str, full_name: str, alert: dict) -> bool:
    level_text = LEVEL_TEXT[alert["level"]]
    subject = f"[Quản lý thu chi] {alert['name']} {level_text}"
    if alert["remaining"] >= 0:
        tail = f"Bạn còn {_vnd(alert['remaining'])} đồng cho danh mục này trong tháng."
    else:
        tail = f"Bạn đã chi vượt {_vnd(-alert['remaining'])} đồng so với hạn mức."
    body = (
        f"Chào {full_name},\n\n"
        f"Danh mục {alert['name']} {level_text} trong tháng {alert['month']}.\n\n"
        f"  Hạn mức : {_vnd(alert['limit'])} đồng\n"
        f"  Đã chi  : {_vnd(alert['spent'])} đồng ({alert['percent']}%)\n\n"
        f"{tail}\n\n"
        "Email này được gửi tự động từ ứng dụng Quản lý thu - chi cá nhân."
    )
    return send_email(to, subject, body)