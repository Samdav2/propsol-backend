from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    name: str
    Status: bool = True
    email_verified: bool = False
    referred_by: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    Status: Optional[bool] = None
    email_verified: Optional[bool] = None
    referred_by: Optional[str] = None

class UserRead(UserBase):
    id: UUID
    referral_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
