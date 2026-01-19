import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, Text
from sqlmodel import SQLModel, Field, ForeignKey, Relationship


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SenderType(str, Enum):
    USER = "user"
    ADMIN = "admin"


class SupportTicket(SQLModel, table=True):
    __tablename__ = "support_ticket"

    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False)
    )
    subject: str = Field(nullable=False, max_length=255)
    status: TicketStatus = Field(default=TicketStatus.OPEN, nullable=False)
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    messages: List["SupportMessage"] = Relationship(back_populates="ticket")
    user: "User" = Relationship(back_populates="support_tickets")


class SupportMessage(SQLModel, table=True):
    __tablename__ = "support_message"

    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    ticket_id: UUID = Field(
        sa_column=Column(ForeignKey("support_ticket.id"), nullable=False)
    )
    sender_id: UUID = Field(nullable=False)
    sender_type: SenderType = Field(nullable=False)
    message: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    ticket: SupportTicket = Relationship(back_populates="messages")


# Keep the old Support model for backward compatibility during migration
# This can be removed after data is migrated
class Support(SQLModel, table=True):
    __tablename__ = "support"
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False)
    phone: str = Field(nullable=False)
    message: str = Field(nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
