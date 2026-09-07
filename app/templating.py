from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def vnd(value) -> str:
    """Dinh dang so tien theo kieu Viet Nam: 1234567 -> 1.234.567"""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(value)


templates.env.filters["vnd"] = vnd