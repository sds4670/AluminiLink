from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import require_admin, require_student
from app.models.user import User
from app.services.screener_service import screen_alumni_profile
from app.services.ml.screener import screen_message
from app.schemas.request import ScreenerCheckRequest, ScreenerResult

router = APIRouter(prefix="/api/v1/screener", tags=["screener"])


@router.post("/check", response_model=ScreenerResult)
async def check_message(
    data: ScreenerCheckRequest,
    current_user: User = Depends(require_student),
):
    """
    Preview-only: score a draft outreach message without saving anything.

    curl -X POST http://localhost:8000/api/v1/screener/check \\
      -H "Authorization: Bearer <student access_token>" -H "Content-Type: application/json" \\
      -d '{"message":"Hi, I would love your guidance on breaking into data science. I saw your experience at your company and wanted to discuss your career journey and learn from your background. Could we schedule a short session?"}'
    """
    return screen_message(data.message)


@router.post("/alumni/{alumni_id}")
async def run_screener(
    alumni_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only alumni profile quality screen (unrelated to message screening above)."""
    report = await screen_alumni_profile(alumni_id, db)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report
