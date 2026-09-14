"""Kiem thu co lap du lieu giua cac tai khoan va tinh toan bao cao."""
from datetime import datetime, timedelta

import pytest

from app.models import Category, Transaction
from app.services import report as svc
from tests.conftest import login, register


@pytest.fixture()
def two_users(client, db_session):
    """Tao hai tai khoan A va B, moi tai khoan mot giao dich rieng."""
    data = {}
    for name in ("userA", "userB"):
        register(client, name)
        login(client, name)

        cat = (
            db_session.query(Category)
            .join(Category.user)
            .filter(Category.name == "Ăn uống")
            .filter(Category.user.has(username=name))
            .first()
        )
        client.post("/transactions", data={
            "amount": "100000" if name == "userA" else "200000",
            "type": "expense",
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "note": f"Giao dich cua {name}",
            "category_id": str(cat.id),
        }, follow_redirects=False)

        tx = (
            db_session.query(Transaction)
            .filter(Transaction.note == f"Giao dich cua {name}")
            .first()
        )
        data[name] = {"category": cat, "transaction": tx}

    # Ket thuc o trang thai dang nhap bang userA
    login(client, "userA")
    return client, data


# ---------- Co lap du lieu ----------

def test_a_khong_xem_duoc_giao_dich_cua_b(two_users):
    """BM-01: Mo bieu mau sua giao dich cua nguoi khac."""
    client, d = two_users
    tx_b = d["userB"]["transaction"]

    r = client.get(f"/transactions?edit={tx_b.id}")

    assert r.status_code == 200
    # Bieu mau trong: khong nap ghi chu cua userB ra
    assert "Giao dich cua userB" not in r.text


def test_a_khong_sua_duoc_giao_dich_cua_b(two_users, db_session):
    """BM-02: Gui yeu cau sua thang vao giao dich cua nguoi khac."""
    client, d = two_users
    tx_b = d["userB"]["transaction"]
    cat_a = d["userA"]["category"]

    r = client.post(f"/transactions/{tx_b.id}/edit", data={
        "amount": "999999",
        "type": "expense",
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "note": "Bi sua trom",
        "category_id": str(cat_a.id),
    }, follow_redirects=False)

    assert r.status_code == 303
    assert "err=notfound" in r.headers["location"]

    db_session.refresh(tx_b)
    assert tx_b.amount == 200000
    assert tx_b.note == "Giao dich cua userB"


def test_a_khong_xoa_duoc_danh_muc_cua_b(two_users, db_session):
    """BM-03: Xoa danh muc cua nguoi khac."""
    client, d = two_users
    cat_b = d["userB"]["category"]

    r = client.post(f"/categories/{cat_b.id}/delete", follow_redirects=False)

    assert r.status_code == 303
    assert "err=notfound" in r.headers["location"]
    assert db_session.query(Category).filter(Category.id == cat_b.id).first() is not None


def test_danh_sach_chi_chua_giao_dich_cua_minh(two_users):
    """BM-04: Danh sach khong lan du lieu tai khoan khac."""
    client, _ = two_users

    r = client.get("/transactions")

    assert "Giao dich cua userA" in r.text
    assert "Giao dich cua userB" not in r.text


def test_bao_cao_chi_tinh_du_lieu_cua_minh(two_users, db_session):
    """BM-05: So lieu bao cao khong cong gop tai khoan khac."""
    client, d = two_users
    user_a = d["userA"]["transaction"].user_id

    s = svc.summary(db_session, user_a)

    assert s["expense"] == 100000  # khong phai 300000
    assert s["count"] == 1


# ---------- Bao cao va tinh toan ----------

def test_tong_thu_chi_va_so_du(auth_client, db_session):
    """BC-01, BC-02: Tinh tong thu, tong chi va so du."""
    cats = {c.name: c for c in db_session.query(Category).all()}
    now = datetime.now()

    for name, amount, type_ in [
        ("Lương", 10_000_000, "income"),
        ("Ăn uống", 2_000_000, "expense"),
        ("Đi lại", 1_000_000, "expense"),
    ]:
        auth_client.post("/transactions", data={
            "amount": str(amount), "type": type_,
            "date": now.strftime("%Y-%m-%dT%H:%M"),
            "note": "", "category_id": str(cats[name].id),
        }, follow_redirects=False)

    user_id = db_session.query(Transaction).first().user_id
    s = svc.summary(db_session, user_id, now.year, now.month)

    assert s["income"] == 10_000_000
    assert s["expense"] == 3_000_000
    assert s["balance"] == 7_000_000
    assert s["count"] == 3


def test_loc_bao_cao_theo_thang(auth_client, db_session):
    """BC-03: Loc theo thang chi lay giao dich trong thang do."""
    cat = db_session.query(Category).filter(Category.name == "Ăn uống").first()
    now = datetime.now()
    truoc = now - timedelta(days=60)

    for dt, amount in [(now, 500_000), (truoc, 900_000)]:
        auth_client.post("/transactions", data={
            "amount": str(amount), "type": "expense",
            "date": dt.strftime("%Y-%m-%dT%H:%M"),
            "note": "", "category_id": str(cat.id),
        }, follow_redirects=False)

    user_id = db_session.query(Transaction).first().user_id

    thang_nay = svc.summary(db_session, user_id, now.year, now.month)
    assert thang_nay["expense"] == 500_000
    assert thang_nay["count"] == 1

    ca_nam = svc.summary(db_session, user_id, now.year, None)
    assert ca_nam["count"] >= 1


def test_bao_cao_khi_chua_co_giao_dich(auth_client, db_session):
    """BC-04: Khong co du lieu thi tra ve 0, khong loi."""
    from app.models import User
    user = db_session.query(User).first()

    s = svc.summary(db_session, user.id)

    assert s == {"income": 0, "expense": 0, "balance": 0, "count": 0}


def test_ty_trong_theo_danh_muc(auth_client, db_session):
    """BC-05: Ty trong chi tieu theo danh muc, sap xep giam dan."""
    cats = {c.name: c for c in db_session.query(Category).all()}
    now = datetime.now()

    for name, amount in [("Ăn uống", 3_000_000), ("Đi lại", 1_000_000)]:
        auth_client.post("/transactions", data={
            "amount": str(amount), "type": "expense",
            "date": now.strftime("%Y-%m-%dT%H:%M"),
            "note": "", "category_id": str(cats[name].id),
        }, follow_redirects=False)

    user_id = db_session.query(Transaction).first().user_id
    rows = svc.by_category(db_session, user_id, "expense", now.year, now.month)

    assert len(rows) == 2
    assert rows[0]["name"] == "Ăn uống"   # lon nhat dung dau
    assert rows[0]["percent"] == 75.0
    assert rows[1]["percent"] == 25.0