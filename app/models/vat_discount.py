import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Column, ForeignKey, Relationship
from sqlalchemy import Enum, BigInteger, DateTime
import enum

class TxnType(str, enum.Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    transfer = "transfer"
    payment = "payment"
    refund = "refund"


class TxnStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    reversed = "reversed"


class DiscountCodes(SQLModel, table=True):
    __tablename__ = "discount_codes"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )

    discount_name: str = Field(nullable=False, index=True)
    discount_code: str = Field(nullable=False, index=True, unique=True)
    percentage: float = Field(nullable=False, index=True)

    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )

class UserDiscount(SQLModel, table=True):
    __tablename__ = "user_discount"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )

    discount_id: uuid.UUID = Field(ForeignKey("discount_codes.id"), nullable=False, index=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False, index=True)
    )
    discount_code: str = Field(nullable=False, index=True, unique=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    user: 'User' = Relationship(back_populates="user_discounts")

class Vat(SQLModel, table=True):
    __tablename__ = "vat"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )

    vat_name: str = Field(nullable=False, index=True)

    percentage: float = Field(nullable=False)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
