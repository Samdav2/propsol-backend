from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

# Vat Schemas
class VatBase(BaseModel):
    vat_name: str
    percentage: float

class VatCreate(VatBase):
    pass

class VatRead(VatBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class VatUpdate(BaseModel):
    vat_name: str | None = None
    percentage: float | None = None

# DiscountCodes Schemas
class DiscountCodesBase(BaseModel):
    discount_name: str
    discount_code: str
    percentage: float
    expires_at: datetime

class DiscountCodesCreate(DiscountCodesBase):
    pass

class DiscountCodesRead(DiscountCodesBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class DiscountCodesUpdate(BaseModel):
    discount_name: str | None = None
    discount_code: str | None = None
    percentage: float | None = None
    expires_at: datetime | None = None

# UserDiscount Schemas
class UserDiscountBase(BaseModel):
    discount_code: str

class UserDiscountCreate(UserDiscountBase):
    pass

class UserDiscountRead(UserDiscountBase):
    id: UUID
    discount_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
