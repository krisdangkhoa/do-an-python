"""Tao du lieu mau cho demo. Chay lai bao nhieu lan cung duoc - se xoa het va tao moi."""
import sys
from datetime import datetime, timedelta

from app.crud import user as crud_user
from app.database import Base, SessionLocal, engine
from app.models import Category, Reminder, Transaction, User
from app.schemas.user import UserCreate

Base.metadata.create_all(bind=engine)

# Nguoi dung phu - tao TRUOC de giao dich cua ho mang ID 1..4,
# tien cho phan demo co lap du lieu.
OTHER = ("linh", "linh@example.com", "Trần Thị Mỹ Linh", "demo123")
MAIN = ("khoa", "khoa@example.com", "Nguyễn Thành Đăng Khoa", "demo123")

EXTRA_CATEGORIES = [
    ("Giải trí", "Xem phim, cà phê, du lịch", "expense"),
    ("Sức khỏe", "Khám bệnh, thuốc men, tập gym", "expense"),
]

# (so ngay truoc hom nay, danh muc, so tien, ghi chu)
MAIN_TX = [
    # Thang 6
    (100, "Lương", 15_000_000, "Lương tháng 6"),
    (99, "Hóa đơn", 1_250_000, "Tiền điện nước tháng 6"),
    (97, "Ăn uống", 2_400_000, "Đi chợ đầu tháng"),
    (94, "Đi lại", 680_000, "Đổ xăng"),
    (90, "Mua sắm", 1_850_000, "Quần áo mùa hè"),
    (87, "Giải trí", 450_000, "Xem phim cuối tuần"),
    (84, "Ăn uống", 1_100_000, None),
    (80, "Thu nhập khác", 2_500_000, "Làm thêm dự án"),
    # Thang 7
    (70, "Lương", 15_000_000, "Lương tháng 7"),
    (69, "Hóa đơn", 1_380_000, "Tiền điện nước tháng 7"),
    (67, "Ăn uống", 2_650_000, "Đi chợ đầu tháng"),
    (64, "Đi lại", 720_000, "Đổ xăng"),
    (61, "Sức khỏe", 950_000, "Khám sức khỏe định kỳ"),
    (58, "Giải trí", 1_200_000, "Đi Vũng Tàu cuối tuần"),
    (55, "Ăn uống", 1_350_000, None),
    (52, "Mua sắm", 640_000, "Đồ dùng gia đình"),
    (50, "Thu nhập khác", 1_800_000, "Thưởng dự án"),
    # Thang 8
    (40, "Lương", 15_000_000, "Lương tháng 8"),
    (39, "Hóa đơn", 1_420_000, "Tiền điện nước tháng 8"),
    (37, "Ăn uống", 2_800_000, "Đi chợ đầu tháng"),
    (35, "Đi lại", 750_000, "Đổ xăng"),
    (32, "Giải trí", 380_000, "Cà phê bạn bè"),
    (30, "Mua sắm", 3_200_000, "Mua điện thoại mới"),
    (27, "Ăn uống", 1_450_000, None),
    (24, "Sức khỏe", 420_000, "Thuốc cảm"),
    (22, "Thu nhập khác", 3_000_000, "Tiền thưởng quý"),
    # Thang 9
    (10, "Lương", 15_000_000, "Lương tháng 9"),
    (9, "Hóa đơn", 1_310_000, "Tiền điện nước tháng 9"),
    (8, "Ăn uống", 2_500_000, "Đi chợ đầu tháng"),
    (6, "Đi lại", 700_000, "Đổ xăng"),
    (5, "Giải trí", 520_000, "Xem phim"),
    (4, "Mua sắm", 890_000, "Sách và văn phòng phẩm"),
    (3, "Ăn uống", 1_180_000, None),
    (2, "Đi lại", 150_000, "Gửi xe tháng"),
    (1, "Ăn uống", 320_000, "Ăn tối"),
]

OTHER_TX = [
    (15, "Lương", 12_000_000, "Lương tháng 9"),
    (12, "Ăn uống", 1_900_000, "Đi chợ"),
    (8, "Hóa đơn", 980_000, "Tiền điện"),
    (3, "Mua sắm", 1_500_000, "Mỹ phẩm"),
]


def wipe(db):
    """Xoa sach du lieu cu."""
    db.query(Transaction).delete()
    db.query(Reminder).delete()
    db.query(Category).delete()
    db.query(User).delete()
    db.commit()
    # Dat lai bo dem ID de moi lan chay cho ra ID giong nhau
    from sqlalchemy import text
    try:
        db.execute(text("DELETE FROM sqlite_sequence"))
        db.commit()
    except Exception:
        db.rollback()


def make_user(db, info):
    username, email, full_name, password = info
    return crud_user.create(db, UserCreate(
        username=username, email=email,
        full_name=full_name, password=password,
    ))


def cat_map(db, user_id):
    rows = db.query(Category).filter(Category.user_id == user_id).all()
    return {c.name: c for c in rows}


def add_transactions(db, user, rows, today):
    cats = cat_map(db, user.id)
    for days_ago, cat_name, amount, note in rows:
        cat = cats[cat_name]
        db.add(Transaction(
            amount=amount,
            type=cat.type,
            date=today - timedelta(days=days_ago),
            note=note,
            category_id=cat.id,
            user_id=user.id,
        ))
    db.commit()


def main():
    db = SessionLocal()
    try:
        wipe(db)
        today = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)

        # --- Nguoi dung phu (tao truoc) ---
        other = make_user(db, OTHER)
        add_transactions(db, other, OTHER_TX, today)
        other_first_tx = (
            db.query(Transaction)
            .filter(Transaction.user_id == other.id)
            .order_by(Transaction.id)
            .first()
        )

        # --- Nguoi dung chinh ---
        main_user = make_user(db, MAIN)
        for name, desc, type_ in EXTRA_CATEGORIES:
            db.add(Category(name=name, description=desc,
                            type=type_, user_id=main_user.id))
        db.commit()
        add_transactions(db, main_user, MAIN_TX, today)

        cats = cat_map(db, main_user.id)
        db.add(Reminder(
            message="Đóng tiền nhà", amount=3_500_000, type="expense",
            remind_time=today.replace(day=1) + timedelta(days=32),
            repeat_type="monthly", active=True, auto_add_transaction=True,
            category_id=cats["Hóa đơn"].id, user_id=main_user.id,
        ))
        db.add(Reminder(
            message="Nhận lương hàng tháng", amount=15_000_000, type="income",
            remind_time=today.replace(day=1) + timedelta(days=35),
            repeat_type="monthly", active=True, auto_add_transaction=False,
            category_id=cats["Lương"].id, user_id=main_user.id,
        ))
        db.commit()

        n_tx = db.query(Transaction).filter(
            Transaction.user_id == main_user.id).count()

        print()
        print("=" * 58)
        print("  DA TAO XONG DU LIEU MAU")
        print("=" * 58)
        print(f"  Tai khoan chinh : khoa  / demo123   ({n_tx} giao dich)")
        print(f"  Tai khoan phu   : linh  / demo123   ({len(OTHER_TX)} giao dich)")
        print()
        print("  DUNG CHO PHAN DEMO CO LAP DU LIEU:")
        print(f"  Giao dich ID {other_first_tx.id} thuoc ve tai khoan 'linh'")
        print(f"  Dang nhap bang 'khoa' roi go: /transactions?edit={other_first_tx.id}")
        print("  Ket qua mong doi: bieu mau TRONG, khong nap du lieu cua linh")
        print("=" * 58)
        print()
    finally:
        db.close()


if __name__ == "__main__":
    if "--yes" not in sys.argv:
        print("CANH BAO: lenh nay se XOA TOAN BO du lieu hien co.")
        print("Chay lai voi: python seed_data.py --yes")
        sys.exit(1)
    main()