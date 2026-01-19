from typing import List, Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.support import Support, SupportTicket, SupportMessage, TicketStatus, SenderType
from app.schema.support import (
    SupportCreate, SupportTicketCreate, SupportMessageCreate,
    SupportTicketRead, SupportTicketListItem, SupportMessageRead,
    PaginatedTicketResponse, TicketStatusUpdate
)
from app.repository.support_repo import SupportRepository, SupportTicketRepository


class SupportService:
    """Service for legacy Support model (backward compatibility)"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SupportRepository(session)

    async def create_support_ticket(self, support_in: SupportCreate, background_tasks: BackgroundTasks) -> Support:
        support = await self.repo.create(support_in)

        from app.service.mail import send_email
        background_tasks.add_task(
            send_email,
            email_to=support.email,
            subject="Support Request Received",
            template_name="support_receipt.html",
            context={"name": support.name, "message": support.message}
        )
        return support

    async def get_all_messages(self, skip: int = 0, limit: int = 100) -> List[Support]:
        """Get all support messages with pagination"""
        return await self.repo.get_all(skip=skip, limit=limit)


class SupportTicketService:
    """Service for the new ticket-based support system"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SupportTicketRepository(session)

    # ============= User Operations =============

    async def create_ticket(
        self,
        user_id: UUID,
        ticket_data: SupportTicketCreate,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> SupportTicketRead:
        """Create a new support ticket"""
        ticket = await self.repo.create_ticket(
            user_id=user_id,
            subject=ticket_data.subject,
            priority=ticket_data.priority,
            initial_message=ticket_data.message
        )

        # Reload ticket with messages
        ticket = await self.repo.get_ticket_with_user(ticket.id)
        return self._ticket_to_read(ticket)

    async def get_user_tickets(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> PaginatedTicketResponse:
        """Get all tickets for a user with pagination"""
        tickets = await self.repo.get_tickets_by_user(user_id, skip, limit)
        total = await self.repo.count_tickets(user_id=user_id)

        items = [self._ticket_to_list_item(t) for t in tickets]
        return PaginatedTicketResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )

    async def get_ticket_details(
        self,
        ticket_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> SupportTicketRead:
        """Get ticket details with messages. Validates access for non-admins."""
        ticket = await self.repo.get_ticket_with_user(ticket_id)

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Non-admins can only view their own tickets
        if not is_admin and ticket.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this ticket"
            )

        return self._ticket_to_read(ticket)

    async def add_message(
        self,
        ticket_id: UUID,
        sender_id: UUID,
        sender_type: SenderType,
        message_data: SupportMessageCreate,
        is_admin: bool = False
    ) -> SupportMessageRead:
        """Add a message to a ticket. Validates access."""
        ticket = await self.repo.get_ticket_by_id(ticket_id)

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Non-admins can only message on their own tickets
        if not is_admin and ticket.user_id != sender_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this ticket"
            )

        # Cannot add messages to closed tickets
        if ticket.status == TicketStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add messages to closed tickets"
            )

        message = await self.repo.add_message(
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message_content=message_data.message
        )

        return SupportMessageRead(
            id=message.id,
            ticket_id=message.ticket_id,
            sender_id=message.sender_id,
            sender_type=message.sender_type,
            message=message.message,
            created_at=message.created_at
        )

    # ============= Admin Operations =============

    async def get_all_tickets(
        self,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[TicketStatus] = None
    ) -> PaginatedTicketResponse:
        """Get all tickets for admin view"""
        tickets = await self.repo.get_all_tickets(skip, limit, status_filter)
        total = await self.repo.count_tickets(status=status_filter)

        items = [self._ticket_to_list_item(t) for t in tickets]
        return PaginatedTicketResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )

    async def update_ticket_status(
        self,
        ticket_id: UUID,
        status_update: TicketStatusUpdate
    ) -> SupportTicketRead:
        """Admin updates ticket status"""
        ticket = await self.repo.update_ticket_status(ticket_id, status_update.status)

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )

        # Reload with user info
        ticket = await self.repo.get_ticket_with_user(ticket_id)
        return self._ticket_to_read(ticket)

    # ============= Helper Methods =============

    def _ticket_to_read(self, ticket: SupportTicket) -> SupportTicketRead:
        """Convert ticket model to read schema"""
        messages = [
            SupportMessageRead(
                id=m.id,
                ticket_id=m.ticket_id,
                sender_id=m.sender_id,
                sender_type=m.sender_type,
                message=m.message,
                created_at=m.created_at
            )
            for m in sorted(ticket.messages, key=lambda x: x.created_at)
        ] if ticket.messages else []

        user_name = None
        user_email = None
        if hasattr(ticket, 'user') and ticket.user:
            user_name = ticket.user.name
            user_email = ticket.user.email

        return SupportTicketRead(
            id=ticket.id,
            user_id=ticket.user_id,
            subject=ticket.subject,
            status=ticket.status,
            priority=ticket.priority,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            messages=messages,
            user_name=user_name,
            user_email=user_email
        )

    def _ticket_to_list_item(self, ticket: SupportTicket) -> SupportTicketListItem:
        """Convert ticket model to list item schema"""
        user_name = None
        user_email = None
        if hasattr(ticket, 'user') and ticket.user:
            user_name = ticket.user.name
            user_email = ticket.user.email

        return SupportTicketListItem(
            id=ticket.id,
            user_id=ticket.user_id,
            subject=ticket.subject,
            status=ticket.status,
            priority=ticket.priority,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            message_count=len(ticket.messages) if ticket.messages else 0,
            user_name=user_name,
            user_email=user_email
        )
