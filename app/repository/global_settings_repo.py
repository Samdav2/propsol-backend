from decimal import Decimal
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.global_affiliate_settings import GlobalAffiliateSettings
from app.repository.base_repo import BaseRepository


class GlobalSettingsRepository(BaseRepository[GlobalAffiliateSettings, dict, dict]):
    """Repository for GlobalAffiliateSettings operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(GlobalAffiliateSettings, session)

    async def get_settings(self) -> GlobalAffiliateSettings:
        """Get global settings (create default if not exists)"""
        query = select(GlobalAffiliateSettings)
        result = await self.session.exec(query)
        settings = result.first()

        if not settings:
            try:
                # Create default settings
                settings = GlobalAffiliateSettings(
                    default_commission_rate=Decimal("0.02"),
                    minimum_withdrawal_amount=Decimal("100.00"),
                    is_program_enabled=True
                )
                self.session.add(settings)
                await self.session.commit()
                await self.session.refresh(settings)
            except Exception:
                await self.session.rollback()
                # Retry fetch
                result = await self.session.exec(query)
                settings = result.first()

        return settings
