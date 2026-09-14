"""Kiem thu chuc nang dang ky, dang nhap va kiem soat truy cap."""
from app.models import Category, User
from tests.conftest import login, register


def test_dang_ky_thanh_cong(client, db_session):
    """TK-01: Dang ky voi thong tin hop le."""
    r = register(client, "khoa1")

    assert r.status_code == 303
    assert "/login" in r.headers["location"]

    user = db_session.query(User).filter(User.username == "khoa1").first()
    assert user is not None
    # Mat khau phai duoc bam, khong luu dang van ban thuan
    assert user.hashed_password != "matkhau123"
    assert user.hashed_password.startswith("$2b$")

    # Tai khoan moi duoc tao san 6 danh muc mac dinh
    n = db_session.query(Category).filter(Category.user_id == user.id).count()
    assert n == 6


def test_dang_ky_trung_ten_bi_tu_choi(client, db_session):
    """TK-02: Ten dang nhap da ton tai."""
    register(client, "khoa1")
    r = register(client, "khoa1", email="khac@example.com")

    assert r.status_code == 400
    assert "đã được sử dụng" in r.text
    assert db_session.query(User).filter(User.username == "khoa1").count() == 1


def test_dang_ky_mat_khau_khong_khop(client, db_session):
    """TK-03: Hai lan nhap mat khau khac nhau."""
    r = client.post("/register", data={
        "username": "khoa2",
        "email": "khoa2@example.com",
        "full_name": "Nguyen Van A",
        "password": "matkhau123",
        "password2": "matkhaukhac",
    }, follow_redirects=False)

    assert r.status_code == 400
    assert "không khớp" in r.text
    assert db_session.query(User).filter(User.username == "khoa2").first() is None


def test_dang_nhap_dung_thong_tin(client):
    """TK-04: Dang nhap thanh cong va tao phien lam viec."""
    register(client, "khoa3")
    r = login(client, "khoa3")

    assert r.status_code == 303
    assert r.headers["location"] == "/"

    # Phien lam viec da duoc tao, truy cap trang chu khong bi chuyen huong
    home = client.get("/", follow_redirects=False)
    assert home.status_code == 200


def test_dang_nhap_sai_mat_khau(client):
    """TK-05: Sai mat khau phai bi tu choi."""
    register(client, "khoa4")
    r = login(client, "khoa4", password="saibet")

    assert r.status_code == 400
    # Thong bao chung chung, khong tiet lo ten dang nhap co ton tai hay khong
    assert "Tên đăng nhập hoặc mật khẩu không đúng" in r.text


def test_chua_dang_nhap_bi_chuyen_ve_trang_login(client):
    """TK-06: Moi trang noi bo deu yeu cau dang nhap."""
    for path in ["/", "/transactions", "/categories", "/report", "/reminders"]:
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 303, f"{path} khong chuyen huong"
        assert "/login" in r.headers["location"], f"{path} chuyen sai dich"