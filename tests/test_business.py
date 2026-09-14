"""Kiem thu nghiep vu giao dich va danh mục."""
from datetime import datetime

from app.models import Category, Transaction


def _cat(db, client, name="Ăn uống"):
    """Lay mot danh muc mac dinh cua tai khoan dang dang nhap."""
    return db.query(Category).filter(Category.name == name).first()


def _add_tx(client, cat_id, amount="250000", type_="expense", note="Test"):
    return client.post("/transactions", data={
        "amount": amount,
        "type": type_,
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "note": note,
        "category_id": str(cat_id),
    }, follow_redirects=False)


# ---------- Giao dich ----------

def test_them_giao_dich_hop_le(auth_client, db_session):
    """GD-01: Them giao dich voi day du thong tin."""
    cat = _cat(db_session, auth_client)
    r = _add_tx(auth_client, cat.id, "250000")

    assert r.status_code == 303
    tx = db_session.query(Transaction).first()
    assert tx is not None
    assert tx.amount == 250000
    assert tx.type == "expense"


def test_so_tien_khong_duong_bi_tu_choi(auth_client, db_session):
    """GD-02: So tien bang 0 hoac am deu bi tu choi."""
    cat = _cat(db_session, auth_client)

    for bad in ["0", "-100"]:
        r = _add_tx(auth_client, cat.id, bad)
        assert r.status_code == 400, f"So tien {bad} le ra phai bi tu choi"

    assert db_session.query(Transaction).count() == 0


def test_so_tien_co_dau_cham_van_luu_duoc(auth_client, db_session):
    """GD-02b: Chap nhan dinh dang 1.200.000"""
    cat = _cat(db_session, auth_client)
    r = _add_tx(auth_client, cat.id, "1.200.000")

    assert r.status_code == 303
    assert db_session.query(Transaction).first().amount == 1_200_000


def test_danh_muc_sai_loai_bi_tu_choi(auth_client, db_session):
    """GD-03: Khong the gan khoan chi vao danh muc thu nhap."""
    luong = _cat(db_session, auth_client, "Lương")  # danh muc thu nhap

    r = _add_tx(auth_client, luong.id, "250000", type_="expense")

    assert r.status_code == 400
    assert "không thuộc loại" in r.text
    assert db_session.query(Transaction).count() == 0


def test_cap_nhat_giao_dich(auth_client, db_session):
    """GD-04: Sua giao dich da co."""
    cat = _cat(db_session, auth_client)
    _add_tx(auth_client, cat.id, "250000")
    tx = db_session.query(Transaction).first()

    r = auth_client.post(f"/transactions/{tx.id}/edit", data={
        "amount": "500000",
        "type": "expense",
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "note": "Da sua",
        "category_id": str(cat.id),
    }, follow_redirects=False)

    assert r.status_code == 303
    db_session.refresh(tx)
    assert tx.amount == 500000
    assert tx.note == "Da sua"


def test_xoa_giao_dich(auth_client, db_session):
    """GD-05: Xoa giao dich."""
    cat = _cat(db_session, auth_client)
    _add_tx(auth_client, cat.id)
    tx = db_session.query(Transaction).first()

    r = auth_client.post(f"/transactions/{tx.id}/delete", follow_redirects=False)

    assert r.status_code == 303
    assert db_session.query(Transaction).count() == 0


# ---------- Danh muc ----------

def test_them_danh_muc_trung_ten_bi_tu_choi(auth_client, db_session):
    """DM-01: Trung ten trong cung mot tai khoan."""
    before = db_session.query(Category).count()

    r = auth_client.post("/categories", data={
        "name": "Ăn uống",  # da ton tai trong danh muc mac dinh
        "description": "",
        "type": "expense",
    }, follow_redirects=False)

    assert r.status_code == 400
    assert "đã tồn tại" in r.text
    assert db_session.query(Category).count() == before


def test_xoa_danh_muc_dang_dung_bi_chan(auth_client, db_session):
    """DM-03: Khong cho xoa danh muc dang co giao dich."""
    cat = _cat(db_session, auth_client)
    _add_tx(auth_client, cat.id)

    r = auth_client.post(f"/categories/{cat.id}/delete", follow_redirects=False)

    assert r.status_code == 303
    assert "err=inuse" in r.headers["location"]
    assert db_session.query(Category).filter(Category.id == cat.id).first() is not None


def test_xoa_danh_muc_chua_dung_thanh_cong(auth_client, db_session):
    """DM-04: Danh muc chua duoc su dung thi xoa duoc."""
    r = auth_client.post("/categories", data={
        "name": "Giải trí",
        "description": "Xem phim",
        "type": "expense",
    }, follow_redirects=False)
    assert r.status_code == 303

    cat = db_session.query(Category).filter(Category.name == "Giải trí").first()
    r = auth_client.post(f"/categories/{cat.id}/delete", follow_redirects=False)

    assert r.status_code == 303
    assert "ok=deleted" in r.headers["location"]
    assert db_session.query(Category).filter(Category.name == "Giải trí").first() is None