from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class UserPurchasedPackageBase(BaseModel):
    package_name: str
    amount: float
    status: str = "active"

class UserPurchasedPackageCreate(UserPurchasedPackageBase):
    user_id: UUID

class UserPurchasedPackageRead(UserPurchasedPackageBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
