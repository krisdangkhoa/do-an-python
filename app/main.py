from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
from app.deps import NotAuthenticated
from app.routers import auth, category, reminder, report, transaction
from app.services import scheduler as sched

import app.models  # noqa: F401 - dang ky model truoc khi tao bang

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khoi dong scheduler khi ung dung chay, dung khi thoat."""
    sched.start()
    yield
    sched.shutdown()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(report.router)
app.include_router(category.router)
app.include_router(transaction.router)
app.include_router(reminder.router)


@app.exception_handler(NotAuthenticated)
def redirect_to_login(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)