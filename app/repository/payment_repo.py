from uuid import UUID
from typing import List
from sqlmodel import select
from app.models.payment import Payment
from app.schema.payment import PaymentCreate, PaymentUpdate
from app.repository.base_repo import BaseRepository

class PaymentRepository(BaseRepository[Payment, PaymentCreate, PaymentUpdate]):
    async def get_by_user(self, user_id: UUID) -> List[Payment]:
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.exec(query)
        return result.all()
