from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr

class SupportBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    message: str

class SupportCreate(SupportBase):
    pass

class SupportRead(SupportBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
