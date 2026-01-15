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


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )


    users_id: uuid.UUID = Field(
        sa_column=Column("users_id", ForeignKey("user.id"), nullable=False)
    )

    type: TxnType = Field(
        sa_column=Column(Enum(TxnType, name="txn_type_enum"), nullable=False, index=True)
    )

    amount_cents: float = Field(
        sa_column=Column(BigInteger, nullable=False)
    )

    status: TxnStatus = Field(
        sa_column=Column(Enum(TxnStatus, name="txn_status_enum"), nullable=False, default=TxnStatus.pending, index=True)
    )

    reference: str = Field(
        default=None,
        nullable=True,
        index=True
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    user: 'User' = Relationship(back_populates="transactions")
