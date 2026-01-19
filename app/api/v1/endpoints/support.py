from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, Query, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_user, get_current_admin
from app.models.admin import Admin
from app.models.user import User
from app.models.support import TicketStatus, SenderType
from app.schema.support import (
    SupportCreate, SupportRead,
    SupportTicketCreate, SupportTicketRead, SupportTicketListItem,
    SupportMessageCreate, SupportMessageRead,
    PaginatedTicketResponse, TicketStatusUpdate
)
from app.service.support_service import SupportService, SupportTicketService

router = APIRouter()


# ============= User Ticket Endpoints =============

@router.post("/tickets", response_model=SupportTicketRead)
async def create_ticket(
    ticket_in: SupportTicketCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Create a new support ticket.
    """
    service = SupportTicketService(session)
    return await service.create_ticket(
        user_id=current_user.id,
        ticket_data=ticket_in,
        background_tasks=background_tasks
    )


@router.get("/tickets", response_model=PaginatedTicketResponse)
async def get_my_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get current user's support tickets.
    """
    service = SupportTicketService(session)
    return await service.get_user_tickets(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.get("/tickets/{ticket_id}", response_model=SupportTicketRead)
async def get_ticket_details(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get ticket details with all messages.
    """
    service = SupportTicketService(session)
    return await service.get_ticket_details(
        ticket_id=ticket_id,
        user_id=current_user.id,
        is_admin=False
    )


@router.post("/tickets/{ticket_id}/messages", response_model=SupportMessageRead)
async def send_message(
    ticket_id: UUID,
    message_in: SupportMessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Send a message on a ticket.
    """
    service = SupportTicketService(session)
    return await service.add_message(
        ticket_id=ticket_id,
        sender_id=current_user.id,
        sender_type=SenderType.USER,
        message_data=message_in,
        is_admin=False
    )


# ============= Admin Ticket Endpoints =============

@router.get("/admin/tickets", response_model=PaginatedTicketResponse)
async def get_all_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get all support tickets (Admin only).
    """
    service = SupportTicketService(session)
    return await service.get_all_tickets(
        skip=skip,
        limit=limit,
        status_filter=status_filter
    )


@router.get("/admin/tickets/{ticket_id}", response_model=SupportTicketRead)
async def admin_get_ticket_details(
    ticket_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get ticket details (Admin only).
    """
    service = SupportTicketService(session)
    return await service.get_ticket_details(
        ticket_id=ticket_id,
        is_admin=True
    )


@router.post("/admin/tickets/{ticket_id}/messages", response_model=SupportMessageRead)
async def admin_send_message(
    ticket_id: UUID,
    message_in: SupportMessageCreate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Admin sends a message on a ticket.
    """
    service = SupportTicketService(session)
    return await service.add_message(
        ticket_id=ticket_id,
        sender_id=current_admin.id,
        sender_type=SenderType.ADMIN,
        message_data=message_in,
        is_admin=True
    )


@router.patch("/admin/tickets/{ticket_id}/status", response_model=SupportTicketRead)
async def update_ticket_status(
    ticket_id: UUID,
    status_update: TicketStatusUpdate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Update ticket status (Admin only).
    """
    service = SupportTicketService(session)
    return await service.update_ticket_status(
        ticket_id=ticket_id,
        status_update=status_update
    )


# ============= Legacy Endpoints (for backward compatibility) =============

@router.post("/", response_model=SupportRead)
async def create_support_message(
    support_in: SupportCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Create a new support message (legacy endpoint).
    """
    service = SupportService(session)
    return await service.create_support_ticket(support_in, background_tasks)


@router.get("", response_model=list[SupportRead])
async def get_all_support_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get all support messages (Admin only, legacy endpoint).
    """
    service = SupportService(session)
    return await service.get_all_messages(skip=skip, limit=limit)
