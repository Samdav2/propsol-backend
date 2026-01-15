from uuid import UUID
from typing import List, Optional
from sqlmodel import select
from app.models.vat_discount import Vat, DiscountCodes, UserDiscount
from app.schema.vat_discount import VatCreate, VatUpdate, DiscountCodesCreate, DiscountCodesUpdate, UserDiscountCreate
from app.repository.base_repo import BaseRepository

class VatRepository(BaseRepository[Vat, VatCreate, VatUpdate]):
    pass

class DiscountCodesRepository(BaseRepository[DiscountCodes, DiscountCodesCreate, DiscountCodesUpdate]):
    async def get_by_code(self, code: str) -> Optional[DiscountCodes]:
        query = select(self.model).where(self.model.discount_code == code)
        result = await self.session.exec(query)
        return result.first()

class UserDiscountRepository(BaseRepository[UserDiscount, UserDiscountCreate, UserDiscountCreate]): # No update for UserDiscount usually
    async def get_by_user(self, user_id: UUID) -> List[UserDiscount]:
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.exec(query)
        return result.all()

    async def get_by_user_and_code(self, user_id: UUID, code: str) -> Optional[UserDiscount]:
        query = select(self.model).where(self.model.user_id == user_id, self.model.discount_code == code)
        result = await self.session.exec(query)
        return result.first()
