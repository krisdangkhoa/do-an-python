from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
from app.deps import NotAuthenticated, get_current_user
from app.models import User
from app.routers import auth, category, transaction
from app.templating import templates

import app.models  # noqa: F401 - dang ky model truoc khi tao bang

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(category.router)
app.include_router(transaction.router)


@app.exception_handler(NotAuthenticated)
def redirect_to_login(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.get("/")
def home(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "home.html", {"request": request, "user": user, "active": "home"}
    )