"""Cau hinh chung cho toan bo bo kiem thu."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services import mailer


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch):
    """Khong bao gio gui email that khi kiem thu: ghi lai vao danh sach."""
    sent = []

    def fake_send(to, subject, body):
        sent.append({"to": to, "subject": subject, "body": body})
        return True

    monkeypatch.setattr(mailer, "send_email", fake_send)
    return sent


@pytest.fixture()
def db_session():
    """Co so du lieu tam trong bo nho, tao moi cho tung test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """TestClient dung co so du lieu tam thay vi CSDL that."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register(client, username="user1", email=None, password="matkhau123"):
    """Tao mot tai khoan qua giao dien dang ky."""
    return client.post("/register", data={
        "username": username,
        "email": email or f"{username}@example.com",
        "full_name": f"Nguoi dung {username}",
        "password": password,
        "password2": password,
    }, follow_redirects=False)


def login(client, username="user1", password="matkhau123"):
    """Dang nhap, tra ve response."""
    return client.post("/login", data={
        "username": username,
        "password": password,
    }, follow_redirects=False)


@pytest.fixture()
def auth_client(client):
    """Client da dang nhap san bang tai khoan user1."""
    register(client)
    login(client)
    return client