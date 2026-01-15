import secrets
import string
from datetime import datetime, timezone
import uuid
from pydantic import EmailStr
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, ForeignKey, Relationship
from uuid import UUID
from enum import Enum





class AccountStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    passed = "passed"
    failed = "failed"

class PaymentStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class PropFirmRegistration(SQLModel, table=True):
    __tablename__ = "prop_firm_registration"
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False)
    )
    login_id: str = Field(nullable=False)
    password: str = Field(nullable=False)
    propfirm_name: str = Field(nullable=False)
    propfirm_website_link: str = Field(nullable=False)
    server_name: str = Field(nullable=False)
    server_type: str = Field(nullable=False)
    challenges_step: int = Field(nullable=False)
    service_scope: int = Field(nullable=True)
    order_id: str = Field(nullable=False)
    propfirm_account_cost: float = Field(nullable=False)
    account_size: float = Field(nullable=False)
    account_phases: int = Field(nullable=False)
    trading_platform: str = Field(nullable=False)
    propfirm_rules: str = Field(nullable=False)
    whatsapp_no: str = Field(nullable=False)
    telegram_username: str = Field(nullable=False)
    account_status: AccountStatus = Field(default=AccountStatus.pending, nullable=False)
    payment_status: PaymentStatus = Field(default=PaymentStatus.pending, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    user: 'User' = Relationship(back_populates="prop_firm_registrations")
