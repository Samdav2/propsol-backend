from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models.support import TicketStatus, TicketPriority, SenderType


# ============= Message Schemas =============

class SupportMessageCreate(BaseModel):
    """Schema for creating a new message on a ticket"""
    message: str


class SupportMessageRead(BaseModel):
    """Schema for reading a message"""
    id: UUID
    ticket_id: UUID
    sender_id: UUID
    sender_type: SenderType
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Ticket Schemas =============

class SupportTicketCreate(BaseModel):
    """Schema for creating a new support ticket"""
    subject: str
    message: str  # Initial message content
    priority: TicketPriority = TicketPriority.MEDIUM


class SupportTicketListItem(BaseModel):
    """Schema for ticket list view (without messages)"""
    id: UUID
    user_id: UUID
    subject: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


class SupportTicketRead(BaseModel):
    """Schema for full ticket view with messages"""
    id: UUID
    user_id: UUID
    subject: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
    messages: List[SupportMessageRead] = []
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


class TicketStatusUpdate(BaseModel):
    """Schema for admin to update ticket status"""
    status: TicketStatus


class TicketPriorityUpdate(BaseModel):
    """Schema for admin to update ticket priority"""
    priority: TicketPriority


# ============= Paginated Response =============

class PaginatedTicketResponse(BaseModel):
    """Paginated response for ticket lists"""
    items: List[SupportTicketListItem]
    total: int
    skip: int
    limit: int


# ============= Legacy Support Schemas (for backward compatibility) =============

class SupportBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    message: str


class SupportCreate(SupportBase):
    pass


class SupportRead(SupportBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
