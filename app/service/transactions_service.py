from uuid import UUID
from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.transactions import Transaction
from app.schema.transactions import TransactionCreate, TransactionUpdate
from app.repository.transactions_repo import TransactionRepository

class TransactionService:
    def __init__(self, session: AsyncSession):
        self.repo = TransactionRepository(Transaction, session)

    async def create_transaction(self, transaction_in: TransactionCreate, user_id: UUID) -> Transaction:
        transaction_data = transaction_in.dict()
        transaction_data["users_id"] = user_id
        return await self.repo.create(transaction_data)

    async def get_transactions_by_user(self, user_id: UUID) -> List[Transaction]:
        return await self.repo.get_by_user(user_id)

    async def get_transaction(self, transaction_id: UUID) -> Transaction | None:
        return await self.repo.get(transaction_id)
