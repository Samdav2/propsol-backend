from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.auth import get_current_user, get_current_admin
from app.db.session import get_session
from app.models.user import User
from app.models.admin import Admin
from app.schema.notification import NotificationRead
from app.service.notification_service import NotificationService

router = APIRouter()

@router.get("/my-notifications", response_model=List[NotificationRead])
async def read_my_notifications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = NotificationService(session)
    return await service.get_user_notifications(current_user.id)

@router.get("/admin/notifications", response_model=List[NotificationRead])
async def read_admin_notifications(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    service = NotificationService(session)
    return await service.get_admin_notifications(current_admin.id)

@router.put("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Mark a single notification as read"""
    service = NotificationService(session)
    notification = await service.mark_as_read(notification_id)

    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification

@router.put("/mark-all-read", response_model=dict)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Mark all user notifications as read"""
    service = NotificationService(session)
    count = await service.mark_all_as_read(current_user.id)
    return {"marked_as_read": count}

@router.get("/unread-count", response_model=dict)
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get count of unread notifications"""
    service = NotificationService(session)
    count = await service.get_unread_count(current_user.id)
    return {"unread_count": count}
