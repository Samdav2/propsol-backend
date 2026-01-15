from uuid import UUID
from typing import List
from sqlmodel import select
from app.models.transactions import Transaction
from app.schema.transactions import TransactionCreate, TransactionUpdate
from app.repository.base_repo import BaseRepository

class TransactionRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    async def get_by_user(self, user_id: UUID) -> List[Transaction]:
        query = select(self.model).where(self.model.users_id == user_id)
        result = await self.session.exec(query)
        return result.all()
