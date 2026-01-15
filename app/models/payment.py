
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, ForeignKey, Relationship
from uuid import UUID



class Payment(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False)
    )
    card_name: str = Field(nullable=False, index=True)
    card_number: str = Field(nullable=False)
    card_expiry_date: datetime = Field(nullable=False)
    card_type: str = Field(nullable=False)
    card_cvv: str = Field(nullable=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    user: 'User' = Relationship(back_populates="payments")
