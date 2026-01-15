from typing import Optional
from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.schema.user import UserCreate, UserUpdate
from app.repository.base_repo import BaseRepository

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(self.model).where(self.model.email == email)
        result = await self.session.exec(query)
        return result.first()

    async def get_by_referral_code(self, code: str) -> Optional[User]:
        query = select(self.model).where(self.model.referral_code == code)
        result = await self.session.exec(query)
        return result.first()
