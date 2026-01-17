import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, Numeric
from sqlmodel import Field, SQLModel

class GlobalAffiliateSettings(SQLModel, table=True):
    """Global affiliate settings (Singleton)"""
    __tablename__ = "global_affiliate_settings"

    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)

    # Default commission rate (e.g. 0.02 for 2%)
    default_commission_rate: Decimal = Field(
        sa_column=Column(Numeric(4, 4), nullable=False, default=0.02)
    )

    # Minimum withdrawal amount
    minimum_withdrawal_amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False, default=100.00)
    )

    is_program_enabled: bool = Field(default=True, nullable=False)

    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
