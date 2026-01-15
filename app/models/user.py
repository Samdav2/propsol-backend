import secrets
import string
from datetime import datetime, timezone
import uuid
from typing import List
from pydantic import EmailStr
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, ForeignKey, Relationship
from uuid import UUID
from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

def generate_referral_code(length=12):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for i in range(length))

class User(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    email: EmailStr = Field(unique=True, nullable=False, index=True)
    name: str = Field(nullable=False)
    password: str = Field(nullable=False)
    Status: bool = Field(nullable=False)
    referral_code: str = Field(nullable=False, unique=True, index=True, default_factory=generate_referral_code)
    email_verified: bool = Field(nullable=False,)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    referred_by: str = Field(nullable=True, index=True)
    payments: List['Payment'] = Relationship(back_populates="user")
    crypto_payments: List['CryptoPayment'] = Relationship(back_populates="user")
    user_discounts: List['UserDiscount'] = Relationship(back_populates="user")
    transactions: List['Transaction'] = Relationship(back_populates="user")
    prop_firm_registrations: List['PropFirmRegistration'] = Relationship(back_populates="user")
    purchased_packages: List['UserPurchasedPackage'] = Relationship(back_populates="user")
    notifications: list["Notification"] = Relationship(back_populates="user")
