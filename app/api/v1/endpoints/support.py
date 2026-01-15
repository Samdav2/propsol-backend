from typing import Any
from typing import Any
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_session
from app.schema.support import SupportCreate, SupportRead
from app.service.support_service import SupportService

router = APIRouter()

@router.post("/", response_model=SupportRead)
async def create_support_ticket(
    support_in: SupportCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Create a new support ticket.
    """
    service = SupportService(session)
    return await service.create_support_ticket(support_in, background_tasks)
