from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class PaymentBase(BaseModel):
    card_name: str
    card_number: str
    card_expiry_date: datetime
    card_type: str
    card_cvv: str | None = None

class PaymentCreate(PaymentBase):
    pass

class PaymentRead(PaymentBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

class PaymentUpdate(BaseModel):
    card_name: str | None = None
    card_number: str | None = None
    card_expiry_date: datetime | None = None
    card_type: str | None = None
    card_cvv: str | None = None
