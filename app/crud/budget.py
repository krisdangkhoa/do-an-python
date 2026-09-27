"""Truy van ngan sach. Moi ham deu loc theo user_id."""
from sqlalchemy.orm import Session, joinedload

from app.models import Budget, BudgetAlert, Category


def list_all(db: Session, user_id: int) -> list[Budget]:
    return (
        db.query(Budget)
        .join(Category, Budget.category_id == Category.id)
        .options(joinedload(Budget.category))
        .filter(Budget.user_id == user_id)
        .order_by(Category.name)
        .all()
    )


def get(db: Session, budget_id: int, user_id: int) -> Budget | None:
    return (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == user_id)
        .first()
    )


def get_by_category(db: Session, category_id: int, user_id: int) -> Budget | None:
    return (
        db.query(Budget)
        .filter(Budget.category_id == category_id, Budget.user_id == user_id)
        .first()
    )


def create(db: Session, category_id: int, amount: int, user_id: int) -> Budget:
    obj = Budget(category_id=category_id, amount=amount, user_id=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: Budget, amount: int) -> Budget:
    obj.amount = amount
    # Doi han muc thi lam moi lich su canh bao, de canh bao lai theo han muc moi
    db.query(BudgetAlert).filter(BudgetAlert.budget_id == obj.id).delete()
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: Budget) -> None:
    db.query(BudgetAlert).filter(BudgetAlert.budget_id == obj.id).delete()
    db.delete(obj)
    db.commit()