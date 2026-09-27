from fastapi import Request
from fastapi.templating import Jinja2Templates

_templates = Jinja2Templates(directory="app/templates")


def vnd(value) -> str:
    """Dinh dang so tien theo kieu Viet Nam: 1234567 -> 1.234.567"""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(value)


def pop_flash(request: Request):
    """Lay thong bao mot lan tu session (hien xong thi mat)."""
    return request.session.pop("flash", None)


_templates.env.filters["vnd"] = vnd
_templates.env.globals["pop_flash"] = pop_flash


class Templates:
    """Boc lai de dung duoc ca hai cach goi TemplateResponse."""

    def __init__(self, inner: Jinja2Templates):
        self._inner = inner
        self.env = inner.env

    def TemplateResponse(self, name, context=None, **kwargs):
        request: Request = context.pop("request")
        return self._inner.TemplateResponse(request, name, context, **kwargs)


templates = Templates(_templates)