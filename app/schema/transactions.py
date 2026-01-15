from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.transactions import TxnType, TxnStatus

class TransactionBase(BaseModel):
    type: TxnType
    amount_cents: float
    status: TxnStatus = TxnStatus.pending
    reference: str | None = None

class TransactionCreate(TransactionBase):
    pass

class TransactionRead(TransactionBase):
    id: UUID
    users_id: UUID
    created_at: datetime
    updated_at: datetime

class TransactionUpdate(BaseModel):
    status: TxnStatus | None = None
    reference: str | None = None
