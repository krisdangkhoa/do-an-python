"""Kiem thu gui canh bao qua email khi vuot ngan sach."""
from datetime import datetime

from app.config import settings
from app.models import Budget, Category, User
from app.services import mailer
from tests.conftest import login, register


def _cat(db, username, name="Ăn uống"):
    return (
        db.query(Category).join(User)
        .filter(User.username == username, Category.name == name)
        .first()
    )


def _tx(client, cat_id, amount, follow=False):
    return client.post("/transactions", data={
        "amount": str(amount), "type": "expense",
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "note": "", "category_id": str(cat_id),
    }, follow_redirects=follow)


def _budget(client, cat_id, amount):
    client.post("/budgets", data={"category_id": str(cat_id), "amount": str(amount)},
                follow_redirects=False)


def test_cham_80_phan_tram_thi_gui_email(auth_client, db_session, sent_emails):
    """CB-01: Cham 80% gui email dung nguoi, hien thong bao tren man hinh."""
    cat = _cat(db_session, "user1")
    _budget(auth_client, cat.id, 1_000_000)

    r = _tx(auth_client, cat.id, 850_000, follow=True)

    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "user1@example.com"
    assert "sắp chạm hạn mức" in sent_emails[0]["subject"]
    assert "Đã gửi email cảnh báo" in r.text


def test_moi_muc_chi_gui_mot_lan(auth_client, db_session, sent_emails):
    """CB-02: Khong gui lap lai cung mot muc trong thang."""
    cat = _cat(db_session, "user1")
    _budget(auth_client, cat.id, 1_000_000)

    _tx(auth_client, cat.id, 850_000)   # 85%  -> canh bao
    _tx(auth_client, cat.id, 50_000)    # 90%  -> van muc canh bao, khong gui lai
    assert len(sent_emails) == 1

    _tx(auth_client, cat.id, 200_000)   # 110% -> vuot, gui email thu hai
    assert len(sent_emails) == 2
    assert "đã vượt hạn mức" in sent_emails[1]["subject"]


def test_khong_co_ngan_sach_thi_khong_gui(auth_client, db_session, sent_emails):
    """CB-03: Danh muc khong dat ngan sach thi khong canh bao."""
    _tx(auth_client, _cat(db_session, "user1").id, 50_000_000)
    assert sent_emails == []


def test_doi_han_muc_thi_duoc_canh_bao_lai(auth_client, db_session, sent_emails):
    """CB-04: Doi han muc lam moi bo dem canh bao."""
    cat = _cat(db_session, "user1")
    _budget(auth_client, cat.id, 1_000_000)
    _tx(auth_client, cat.id, 1_100_000)                 # vuot -> email 1
    b = db_session.query(Budget).first()

    auth_client.post(f"/budgets/{b.id}/edit", data={"amount": "2000000"}, follow_redirects=False)
    _tx(auth_client, cat.id, 1_000_000)                 # 2.100.000 / 2.000.000 -> email 2

    assert len(sent_emails) == 2


def test_chi_gui_cho_chu_tai_khoan(client, db_session, sent_emails):
    """CB-05: Email chi gui toi chu cua ngan sach."""
    register(client, "userA")
    register(client, "userB")
    login(client, "userB")
    cat = _cat(db_session, "userB")
    _budget(client, cat.id, 100_000)
    _tx(client, cat.id, 150_000)

    assert [m["to"] for m in sent_emails] == ["userb@example.com"]  # email duoc chuyen ve chu thuong khi dang ky


def test_chua_cau_hinh_smtp_thi_in_ra_man_hinh(monkeypatch, capsys):
    """CB-06: Khong co SMTP van chay, in noi dung email thay vi bao loi."""
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    ok = mailer.deliver("a@example.com", "Tieu de thu", "Noi dung thu")

    assert ok is False
    assert "Tieu de thu" in capsys.readouterr().out