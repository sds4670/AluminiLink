from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.services.screener_service import screen_alumni_profile

router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.post("/alumni/{alumni_id}")
async def run_screener(
    alumni_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    report = await screen_alumni_profile(alumni_id, db)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report
