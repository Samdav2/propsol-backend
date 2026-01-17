from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.affiliate_settings import AffiliateSettings
from app.repository.base_repo import BaseRepository


class AffiliateSettingsRepository(BaseRepository[AffiliateSettings, dict, dict]):
    """Repository for AffiliateSettings operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(AffiliateSettings, session)

    async def get_by_user_id(self, user_id: UUID) -> Optional[AffiliateSettings]:
        """Get settings by user ID"""
        query = select(AffiliateSettings).where(AffiliateSettings.user_id == user_id)
        result = await self.session.exec(query)
        return result.first()

    async def get_or_create(self, user_id: UUID) -> AffiliateSettings:
        """Get existing settings or create default"""
        settings = await self.get_by_user_id(user_id)
        if not settings:
            try:
                settings = AffiliateSettings(user_id=user_id)
                self.session.add(settings)
                await self.session.commit()
                await self.session.refresh(settings)
            except Exception:
                await self.session.rollback()
                settings = await self.get_by_user_id(user_id)
        return settings
