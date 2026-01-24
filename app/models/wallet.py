import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Text
from sqlmodel import Field, SQLModel, Relationship


class EarningStatus(str, Enum):
    """Status of a referral earning"""
    available = "available"      # Standard pass - immediately available
    locked = "locked"           # Guaranteed pass - locked until challenge passed
    released = "released"       # Guaranteed pass after challenge passed
    claimed = "claimed"         # Already withdrawn


class PaymentMethod(str, Enum):
    """Withdrawal payment methods"""
    bank_transfer = "bank_transfer"
    crypto = "crypto"
    paypal = "paypal"


class WithdrawalStatus(str, Enum):
    """Status of withdrawal request"""
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"


class Wallet(SQLModel, table=True):
    """User's wallet containing balance information"""
    __tablename__ = "wallet"

    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    )
    available_balance: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False, default=0.00)
    )
    locked_balance: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False, default=0.00)
    )
    total_withdrawn: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False, default=0.00)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    referral_earnings: List["ReferralEarning"] = Relationship(back_populates="wallet")
    withdrawal_requests: List["WithdrawalRequest"] = Relationship(back_populates="wallet")


class ReferralEarning(SQLModel, table=True):
    """Individual referral earning record"""
    __tablename__ = "referral_earning"

    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    wallet_id: UUID = Field(
        sa_column=Column(ForeignKey("wallet.id", ondelete="CASCADE"), nullable=False)
    )
    referrer_id: UUID = Field(nullable=False, index=True)  # User who earns the commission
    referred_user_id: UUID = Field(nullable=False, index=True)  # User who used the referral code
    registration_id: Optional[UUID] = Field(nullable=True, index=True)  # PropFirmRegistration ID
    pass_type: str = Field(nullable=False)  # "standard_pass" or "guaranteed_pass"
    amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False)
    )
    status: EarningStatus = Field(default=EarningStatus.locked, nullable=False)
    challenge_passed: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    released_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True),
        default=None
    )

    # Relationships
    wallet: "Wallet" = Relationship(back_populates="referral_earnings")


class WithdrawalRequest(SQLModel, table=True):
    """Withdrawal request record"""
    __tablename__ = "withdrawal_request"

    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    wallet_id: UUID = Field(
        sa_column=Column(ForeignKey("wallet.id", ondelete="CASCADE"), nullable=False)
    )
    amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False)
    )
    payment_method: PaymentMethod = Field(nullable=False)

    # Bank transfer details
    bank_name: Optional[str] = Field(nullable=True)
    account_number: Optional[str] = Field(nullable=True)
    account_name: Optional[str] = Field(nullable=True)
    routing_number: Optional[str] = Field(nullable=True)
    swift_code: Optional[str] = Field(nullable=True)

    # Crypto details
    crypto_wallet_address: Optional[str] = Field(nullable=True)
    crypto_network: Optional[str] = Field(nullable=True)
    crypto_currency: Optional[str] = Field(nullable=True)

    # PayPal details
    paypal_email: Optional[str] = Field(nullable=True)

    status: WithdrawalStatus = Field(default=WithdrawalStatus.pending, nullable=False)
    admin_notes: Optional[str] = Field(
        sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    processed_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True),
        default=None
    )

    # NOWPayments details
    batch_withdrawal_id: Optional[str] = Field(nullable=True, index=True)
    payout_id: Optional[str] = Field(nullable=True, index=True)
    external_status: Optional[str] = Field(nullable=True)
    rejection_reason: Optional[str] = Field(nullable=True)

    # Relationships
    wallet: "Wallet" = Relationship(back_populates="withdrawal_requests")
