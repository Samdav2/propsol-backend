from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, ForeignKey, Relationship
from uuid import UUID


class CryptoPayment(SQLModel, table=True):
    """Model for NOWPayments cryptocurrency payments"""
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False)
    )

    # NOWPayments identifiers
    payment_id: str | None = Field(default=None, index=True, nullable=True)  # NOWPayments payment ID
    invoice_id: str | None = Field(default=None, index=True, nullable=True)  # NOWPayments invoice ID

    # Order information
    order_id: str | None = Field(default=None, nullable=True)
    order_description: str | None = Field(default=None, nullable=True)

    # Price information
    price_amount: float = Field(nullable=False)
    price_currency: str = Field(nullable=False)  # usd, eur, etc

    # Payment information
    pay_amount: float | None = Field(default=None, nullable=True)
    pay_currency: str = Field(nullable=False)  # btc, eth, trx, etc
    pay_address: str | None = Field(default=None, nullable=True)
    payin_extra_id: str | None = Field(default=None, nullable=True)  # For currencies requiring memo/tag

    # Status and tracking
    payment_status: str = Field(default="waiting", nullable=False)  # waiting, confirming, confirmed, sending, partially_paid, finished, failed, expired

    # Additional fields
    actually_paid: float | None = Field(default=None, nullable=True)
    purchase_id: str | None = Field(default=None, nullable=True)
    outcome_amount: float | None = Field(default=None, nullable=True)
    outcome_currency: str | None = Field(default=None, nullable=True)

    # URLs
    ipn_callback_url: str | None = Field(default=None, nullable=True)
    invoice_url: str | None = Field(default=None, nullable=True)

    # Options
    is_fixed_rate: bool = Field(default=False, nullable=False)
    is_fee_paid_by_user: bool = Field(default=False, nullable=False)

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    user: 'User' = Relationship(back_populates="crypto_payments")
