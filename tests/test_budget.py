"""Kiem thu ngan sach va canh bao vuot muc."""
from datetime import datetime

from app.models import Budget, Category, User
from app.services import budget as svc
from tests.conftest import login, register


def _cat(db, username, name):
    return (
        db.query(Category).join(User)
        .filter(User.username == username, Category.name == name)
        .first()
    )


def _add_tx(client, cat_id, amount):
    client.post("/transactions", data={
        "amount": str(amount), "type": "expense",
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "note": "", "category_id": str(cat_id),
    }, follow_redirects=False)


def _add_budget(client, cat_id, amount):
    return client.post("/budgets", data={
        "category_id": str(cat_id), "amount": str(amount),
    }, follow_redirects=False)


def test_tao_ngan_sach_hop_le(auth_client, db_session):
    """NS-01: Dat han muc cho danh muc chi tieu."""
    cat = _cat(db_session, "user1", "Ăn uống")
    r = _add_budget(auth_client, cat.id, "1.000.000")

    assert r.status_code == 303
    assert db_session.query(Budget).first().amount == 1_000_000


def test_chi_dat_ngan_sach_cho_danh_muc_chi_tieu(auth_client, db_session):
    """NS-02: Danh muc thu nhap bi tu choi."""
    luong = _cat(db_session, "user1", "Lương")
    r = _add_budget(auth_client, luong.id, 5_000_000)

    assert r.status_code == 400
    assert "Chỉ đặt ngân sách cho danh mục chi tiêu" in r.text
    assert db_session.query(Budget).count() == 0


def test_moi_danh_muc_chi_mot_ngan_sach(auth_client, db_session):
    """NS-03: Khong tao hai ngan sach cho cung mot danh muc."""
    cat = _cat(db_session, "user1", "Ăn uống")
    _add_budget(auth_client, cat.id, 1_000_000)
    r = _add_budget(auth_client, cat.id, 2_000_000)

    assert r.status_code == 400
    assert db_session.query(Budget).count() == 1


def test_han_muc_khong_duong_bi_tu_choi(auth_client, db_session):
    """NS-04: Han muc bang 0 bi tu choi."""
    cat = _cat(db_session, "user1", "Ăn uống")
    r = _add_budget(auth_client, cat.id, "0")

    assert r.status_code == 400
    assert db_session.query(Budget).count() == 0


def test_canh_bao_theo_muc_da_chi(auth_client, db_session):
    """NS-05: Du 80% thi canh bao, du 100% thi bao vuot."""
    cat = _cat(db_session, "user1", "Ăn uống")
    user_id = cat.user_id
    _add_budget(auth_client, cat.id, 1_000_000)

    _add_tx(auth_client, cat.id, 500_000)
    assert svc.status(db_session, user_id)[0]["level"] == "ok"

    _add_tx(auth_client, cat.id, 350_000)          # tong 850.000 = 85%
    row = svc.status(db_session, user_id)[0]
    assert row["level"] == "warning"
    assert row["percent"] == 85.0

    _add_tx(auth_client, cat.id, 200_000)          # tong 1.050.000 = 105%
    row = svc.status(db_session, user_id)[0]
    assert row["level"] == "over"
    assert row["remaining"] == -50_000
    assert len(svc.alerts(db_session, user_id)) == 1


def test_khong_sua_xoa_duoc_ngan_sach_nguoi_khac(client, db_session):
    """NS-06: Co lap du lieu ngan sach giua cac tai khoan."""
    register(client, "userB")
    login(client, "userB")
    _add_budget(client, _cat(db_session, "userB", "Ăn uống").id, 1_000_000)
    b = db_session.query(Budget).first()

    register(client, "userA")
    login(client, "userA")
    r1 = client.post(f"/budgets/{b.id}/edit", data={"amount": "1"}, follow_redirects=False)
    r2 = client.post(f"/budgets/{b.id}/delete", follow_redirects=False)

    assert "err=notfound" in r1.headers["location"]
    assert "err=notfound" in r2.headers["location"]
    db_session.refresh(b)
    assert b.amount == 1_000_000


def test_xoa_danh_muc_xoa_luon_ngan_sach(auth_client, db_session):
    """NS-07: Khong de lai ngan sach mo coi."""
    auth_client.post("/categories", data={
        "name": "Giải trí", "description": "", "type": "expense",
    }, follow_redirects=False)
    cat = _cat(db_session, "user1", "Giải trí")
    _add_budget(auth_client, cat.id, 500_000)
    assert db_session.query(Budget).count() == 1

    auth_client.post(f"/categories/{cat.id}/delete", follow_redirects=False)

    assert db_session.query(Budget).count() == 0