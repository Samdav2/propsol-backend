from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.support import Support, SupportTicket, SupportMessage, TicketStatus, SenderType
from app.models.user import User
from app.schema.support import SupportCreate, SupportTicketCreate
from app.repository.base_repo import BaseRepository


class SupportRepository(BaseRepository[Support, SupportCreate, SupportCreate]):
    """Repository for legacy Support model (backward compatibility)"""

    def __init__(self, session: AsyncSession):
        super().__init__(Support, session)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Support]:
        """Get all support messages with pagination"""
        query = select(Support).order_by(Support.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.exec(query)
        return list(result.all())

    async def count_all(self) -> int:
        """Count all support messages"""
        query = select(func.count()).select_from(Support)
        result = await self.session.exec(query)
        return result.one()


class SupportTicketRepository:
    """Repository for SupportTicket and SupportMessage operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============= Ticket Operations =============

    async def create_ticket(
        self,
        user_id: UUID,
        subject: str,
        priority: str,
        initial_message: str
    ) -> SupportTicket:
        """Create a new support ticket with an initial message"""
        ticket = SupportTicket(
            user_id=user_id,
            subject=subject,
            priority=priority,
            status=TicketStatus.OPEN
        )
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)

        # Create initial message
        message = SupportMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            sender_type=SenderType.USER,
            message=initial_message
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(ticket)

        return ticket

    async def get_ticket_by_id(self, ticket_id: UUID) -> Optional[SupportTicket]:
        """Get a ticket by ID with messages loaded"""
        query = (
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .options(selectinload(SupportTicket.messages))
        )
        result = await self.session.exec(query)
        return result.first()

    async def get_ticket_with_user(self, ticket_id: UUID) -> Optional[SupportTicket]:
        """Get a ticket by ID with user and messages loaded"""
        query = (
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .options(
                selectinload(SupportTicket.messages),
                selectinload(SupportTicket.user)
            )
        )
        result = await self.session.exec(query)
        return result.first()

    async def get_tickets_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[SupportTicket]:
        """Get all tickets for a user"""
        query = (
            select(SupportTicket)
            .where(SupportTicket.user_id == user_id)
            .options(selectinload(SupportTicket.messages))
            .order_by(SupportTicket.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(query)
        return list(result.all())

    async def get_all_tickets(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[TicketStatus] = None
    ) -> List[SupportTicket]:
        """Get all tickets (admin view) with optional status filter"""
        query = select(SupportTicket).options(
            selectinload(SupportTicket.messages),
            selectinload(SupportTicket.user)
        )

        if status:
            query = query.where(SupportTicket.status == status)

        query = query.order_by(SupportTicket.updated_at.desc()).offset(skip).limit(limit)
        result = await self.session.exec(query)
        return list(result.all())

    async def count_tickets(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[TicketStatus] = None
    ) -> int:
        """Count tickets with optional filters"""
        query = select(func.count()).select_from(SupportTicket)

        if user_id:
            query = query.where(SupportTicket.user_id == user_id)
        if status:
            query = query.where(SupportTicket.status == status)

        result = await self.session.exec(query)
        return result.one()

    async def update_ticket_status(
        self,
        ticket_id: UUID,
        status: TicketStatus
    ) -> Optional[SupportTicket]:
        """Update a ticket's status"""
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            return None

        ticket.status = status
        ticket.updated_at = datetime.now(timezone.utc)
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def update_ticket_priority(
        self,
        ticket_id: UUID,
        priority: str
    ) -> Optional[SupportTicket]:
        """Update a ticket's priority"""
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            return None

        ticket.priority = priority
        ticket.updated_at = datetime.now(timezone.utc)
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    # ============= Message Operations =============

    async def add_message(
        self,
        ticket_id: UUID,
        sender_id: UUID,
        sender_type: SenderType,
        message_content: str
    ) -> SupportMessage:
        """Add a message to a ticket"""
        message = SupportMessage(
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message=message_content
        )
        self.session.add(message)

        # Update ticket's updated_at timestamp
        ticket = await self.get_ticket_by_id(ticket_id)
        if ticket:
            ticket.updated_at = datetime.now(timezone.utc)
            # If admin replies to open ticket, set to in_progress
            if sender_type == SenderType.ADMIN and ticket.status == TicketStatus.OPEN:
                ticket.status = TicketStatus.IN_PROGRESS
            self.session.add(ticket)

        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_messages_for_ticket(self, ticket_id: UUID) -> List[SupportMessage]:
        """Get all messages for a ticket"""
        query = (
            select(SupportMessage)
            .where(SupportMessage.ticket_id == ticket_id)
            .order_by(SupportMessage.created_at.asc())
        )
        result = await self.session.exec(query)
        return list(result.all())
