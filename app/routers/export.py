"""Tai bao cao dang tep Excel."""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.routers.report import _filters
from app.services import export as svc_export

router = APIRouter(tags=["export"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/report/export")
def export_excel(
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    y, m, _ = _filters(db, user, year, month)
    data = svc_export.build_workbook(db, user, y, m)
    name = f"bao-cao-thu-chi-{y}" + (f"-{m:02d}" if m else "") + ".xlsx"
    return Response(
        content=data,
        media_type=XLSX,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )