from typing import Any, List
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
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


@router.get("", response_model=List[SupportRead])
async def get_all_support_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get all support messages (Admin only).
    """
    service = SupportService(session)
    return await service.get_all_messages(skip=skip, limit=limit)
