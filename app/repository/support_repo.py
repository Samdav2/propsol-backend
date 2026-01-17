from typing import List

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.support import Support
from app.schema.support import SupportCreate
from app.repository.base_repo import BaseRepository


class SupportRepository(BaseRepository[Support, SupportCreate, SupportCreate]):

    def __init__(self, session: AsyncSession):
        super().__init__(Support, session)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Support]:
        """Get all support messages with pagination"""
        query = select(Support).order_by(Support.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.exec(query)
        return list(result.all())

    async def count_all(self) -> int:
        """Count all support messages"""
        from sqlalchemy import func
        query = select(func.count()).select_from(Support)
        result = await self.session.exec(query)
        return result.one()
