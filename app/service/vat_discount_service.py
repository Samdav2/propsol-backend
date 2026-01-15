from uuid import UUID
from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.vat_discount import Vat, DiscountCodes, UserDiscount
from app.schema.vat_discount import VatCreate, DiscountCodesCreate, UserDiscountCreate
from app.repository.vat_discount_repo import VatRepository, DiscountCodesRepository, UserDiscountRepository

class VatDiscountService:
    def __init__(self, session: AsyncSession):
        self.vat_repo = VatRepository(Vat, session)
        self.discount_repo = DiscountCodesRepository(DiscountCodes, session)
        self.user_discount_repo = UserDiscountRepository(UserDiscount, session)

    # VAT
    async def create_vat(self, vat_in: VatCreate) -> Vat:
        return await self.vat_repo.create(vat_in)

    async def get_all_vats(self) -> List[Vat]:
        return await self.vat_repo.get_all()

    # Discounts
    async def create_discount_code(self, discount_in: DiscountCodesCreate) -> DiscountCodes:
        existing = await self.get_discount_by_code(discount_in.discount_code)
        if existing:
            raise ValueError("Discount code already exists")
        return await self.discount_repo.create(discount_in)

    async def get_all_discounts(self) -> List[DiscountCodes]:
        return await self.discount_repo.get_all()

    async def get_discount_by_code(self, code: str) -> Optional[DiscountCodes]:
        return await self.discount_repo.get_by_code(code)

    # User Discounts
    async def apply_discount(self, user_id: UUID, discount_code: str) -> UserDiscount:
        discount = await self.discount_repo.get_by_code(discount_code)
        if not discount:
            raise ValueError("Discount code not found")

        existing = await self.user_discount_repo.get_by_user_and_code(user_id, discount_code)
        if existing:
            raise ValueError("Discount code already applied")

        user_discount_in = {
            "user_id": user_id,
            "discount_id": discount.id,
            "discount_code": discount.discount_code
        }
        return await self.user_discount_repo.create(user_discount_in)

    async def get_user_discounts(self, user_id: UUID) -> List[UserDiscount]:
        return await self.user_discount_repo.get_by_user(user_id)
