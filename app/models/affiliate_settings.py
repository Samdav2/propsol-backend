import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Text
from sqlmodel import Field, SQLModel, Relationship

class AffiliateSettings(SQLModel, table=True):
    """Per-user affiliate settings"""
    __tablename__ = "affiliate_settings"

    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    )

    # Custom commission rate (overrides global default if set)
    # e.g. 0.05 for 5%
    custom_commission_rate: Optional[Decimal] = Field(
        sa_column=Column(Numeric(4, 4), nullable=True),
        default=None
    )

    is_affiliate_enabled: bool = Field(default=True, nullable=False)

    notes: Optional[str] = Field(
        sa_column=Column(Text, nullable=True)
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
