from uuid import UUID
from typing import List
from sqlmodel import select
from app.models.crypto_payment import CryptoPayment
from app.schema.crypto_payment import CryptoPaymentCreate, CryptoPaymentUpdate
from app.repository.base_repo import BaseRepository


class CryptoPaymentRepository(BaseRepository[CryptoPayment, CryptoPaymentCreate, CryptoPaymentUpdate]):
    """Repository for CryptoPayment operations"""

    async def get_by_user(self, user_id: UUID) -> List[CryptoPayment]:
        """Get all crypto payments for a specific user"""
        query = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.desc())
        result = await self.session.exec(query)
        return result.all()

    async def get_by_payment_id(self, payment_id: str) -> CryptoPayment | None:
        """Get crypto payment by NOWPayments payment ID"""
        query = select(self.model).where(self.model.payment_id == payment_id)
        result = await self.session.exec(query)
        return result.first()

    async def get_by_invoice_id(self, invoice_id: str) -> CryptoPayment | None:
        """Get crypto payment by NOWPayments invoice ID"""
        query = select(self.model).where(self.model.invoice_id == invoice_id)
        result = await self.session.exec(query)
        return result.first()
