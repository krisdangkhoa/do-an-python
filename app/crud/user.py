"""Truy van va tao tai khoan nguoi dung."""
from sqlalchemy.orm import Session

from app.models import Category, TransactionType, User
from app.schemas.user import UserCreate
from app.security import hash_password, verify_password

# Danh muc tao san khi dang ky, de nguoi dung dung duoc ngay
DEFAULT_CATEGORIES = [
    ("Lương", "Thu nhập chính hàng tháng", TransactionType.INCOME),
    ("Thu nhập khác", "Thưởng, làm thêm, quà tặng", TransactionType.INCOME),
    ("Ăn uống", "Cơm, cà phê, đi chợ", TransactionType.EXPENSE),
    ("Đi lại", "Xăng xe, vé tàu xe, gửi xe", TransactionType.EXPENSE),
    ("Hóa đơn", "Điện, nước, internet, điện thoại", TransactionType.EXPENSE),
    ("Mua sắm", "Quần áo, đồ dùng cá nhân", TransactionType.EXPENSE),
]


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create(db: Session, data: UserCreate) -> User:
    """Tao tai khoan moi kem cac danh muc mac dinh."""
    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.flush()  # lay user.id truoc khi tao danh muc

    for name, desc, ctype in DEFAULT_CATEGORIES:
        db.add(Category(
            name=name, description=desc,
            type=ctype.value, user_id=user.id,
        ))

    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> User | None:
    """Tra ve User neu dung thong tin, nguoc lai tra ve None."""
    user = get_by_username(db, username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None