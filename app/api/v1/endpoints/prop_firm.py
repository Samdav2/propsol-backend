from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schema.propfirm_registration import PropFirmRegistrationCreate, PropFirmRegistrationRead
from app.service.propfirm_registration_service import PropFirmRegistrationService

router = APIRouter()

async def create_registration_notification(user_id: UUID, propfirm_name: str, order_id: str):
    """Background task to create notification for new registration"""
    from app.db.session import async_session_maker
    from app.service.notification_service import NotificationService

    async with async_session_maker() as session:
        notification_service = NotificationService(session)
        await notification_service.create_registration_created_notification(
            user_id=user_id,
            propfirm_name=propfirm_name,
            order_id=order_id
        )
        await session.commit()

@router.post("", response_model=PropFirmRegistrationRead)
async def create_propfirm_registration(
    registration: PropFirmRegistrationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    # Extract user_id early to avoid greenlet issues
    user_id = current_user.id

    service = PropFirmRegistrationService(session)
    new_registration = await service.create_registration(registration, user_id)

    # Schedule notification creation as background task to avoid session issues
    background_tasks.add_task(
        create_registration_notification,
        user_id=user_id,
        propfirm_name=new_registration.propfirm_name,
        order_id=new_registration.order_id
    )

    return new_registration

@router.get("", response_model=List[PropFirmRegistrationRead])
async def read_propfirm_registrations(
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PropFirmRegistrationService(session)
    return await service.get_registrations_by_user(current_user.id, status)

@router.get("/{registration_id}", response_model=PropFirmRegistrationRead)
async def read_propfirm_registration(
    registration_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PropFirmRegistrationService(session)
    registration = await service.get_registration(registration_id)
    if not registration or registration.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Registration not found")
    return registration
