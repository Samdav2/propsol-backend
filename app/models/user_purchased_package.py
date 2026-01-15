from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, ForeignKey, Relationship
from uuid import UUID

class UserPurchasedPackage(SQLModel, table=True):
    __tablename__ = "user_purchased_package"
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("user.id"), nullable=False)
    )
    package_name: str = Field(nullable=False)
    amount: float = Field(nullable=False)
    status: str = Field(default="active", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    user: 'User' = Relationship(back_populates="purchased_packages")
