from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.models.affiliate_settings import AffiliateSettings
from app.repository.wallet_repo import ReferralEarningRepository, WalletRepository
from app.repository.affiliate_settings_repo import AffiliateSettingsRepository
from app.repository.global_settings_repo import GlobalSettingsRepository
from app.repository.user_repo import UserRepository
from app.schema.affiliate_admin import (
    AffiliateDashboardStats, AffiliateUserDetail, TopAffiliateItem,
    ProductAffiliateStats, AffiliateUserListResponse, GlobalSettingsResponse
)
from app.service.wallet_service import COMMISSION_RATE

class AffiliateAdminService:
    """Service for admin affiliate operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.earning_repo = ReferralEarningRepository(session)
        self.wallet_repo = WalletRepository(session)
        self.settings_repo = AffiliateSettingsRepository(session)
        self.global_settings_repo = GlobalSettingsRepository(session)
        self.user_repo = UserRepository(User, session)

    async def get_global_settings(self) -> GlobalSettingsResponse:
        """Get global affiliate settings"""
        settings = await self.global_settings_repo.get_settings()
        return GlobalSettingsResponse(
            default_commission_rate=float(settings.default_commission_rate),
            minimum_withdrawal_amount=float(settings.minimum_withdrawal_amount),
            is_program_enabled=settings.is_program_enabled
        )

    async def update_global_settings(
        self,
        default_commission_rate: Optional[float],
        minimum_withdrawal_amount: Optional[float],
        is_program_enabled: Optional[bool]
    ) -> GlobalSettingsResponse:
        """Update global affiliate settings"""
        settings = await self.global_settings_repo.get_settings()

        if default_commission_rate is not None:
            settings.default_commission_rate = Decimal(str(default_commission_rate))

        if minimum_withdrawal_amount is not None:
            settings.minimum_withdrawal_amount = Decimal(str(minimum_withdrawal_amount))

        if is_program_enabled is not None:
            settings.is_program_enabled = is_program_enabled

        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)

        return await self.get_global_settings()

    async def get_dashboard_stats(self) -> AffiliateDashboardStats:
        """Get overall dashboard statistics"""
        stats = await self.earning_repo.get_total_earnings_stats()

        # Get user counts
        # This is inefficient for large DBs, should use count query in repo
        users = await self.user_repo.get_all()
        total_signups = len(users) # Total users in system

        # Active affiliates (those with earnings)
        top_affiliates = await self.earning_repo.get_top_affiliates(limit=10000)
        active_count = len(top_affiliates)

        return AffiliateDashboardStats(
            total_earnings_paid=float(stats["total_paid"]),
            total_pending_earnings=float(stats["total_pending"]),
            total_signups=total_signups,
            total_referral_volume=float(stats.get("total_volume", 0)), # Placeholder
            active_affiliates_count=active_count,
            conversion_rate=0.0 # Placeholder
        )

    async def get_top_affiliates(self, limit: int = 10) -> List[TopAffiliateItem]:
        """Get top performing affiliates"""
        raw_stats = await self.earning_repo.get_top_affiliates(limit)

        result = []
        for referrer_id, amount, count in raw_stats:
            user = await self.user_repo.get(referrer_id)
            if user:
                result.append(TopAffiliateItem(
                    user_id=user.id,
                    name=user.name,
                    referral_code=user.referral_code,
                    total_earnings=float(amount),
                    total_referrals=count
                ))

        return result

    async def get_product_stats(self) -> List[ProductAffiliateStats]:
        """Get stats by product"""
        raw_stats = await self.earning_repo.get_product_stats()

        result = []
        for item in raw_stats:
            product_name = item["product"].replace("_", " ").title()
            stats = item["stats"]
            result.append(ProductAffiliateStats(
                product_name=product_name,
                total_sales_count=stats["count"],
                total_sales_volume=0.0, # Need purchase amount to calculate accurately
                total_commission_generated=float(stats["commission"])
            ))

        return result

    async def get_affiliate_detail(self, user_id: UUID) -> Optional[AffiliateUserDetail]:
        """Get detailed stats for a user"""
        user = await self.user_repo.get(user_id)
        if not user:
            return None

        wallet = await self.wallet_repo.get_by_user_id(user_id)
        settings = await self.settings_repo.get_by_user_id(user_id)

        total_referrals = await self.earning_repo.count_by_referrer(user_id)

        # Determine current rate
        current_rate = float(COMMISSION_RATE)
        custom_rate = None
        is_enabled = True

        if settings:
            if settings.custom_commission_rate is not None:
                current_rate = float(settings.custom_commission_rate)
                custom_rate = float(settings.custom_commission_rate)
            is_enabled = settings.is_affiliate_enabled

        return AffiliateUserDetail(
            user_id=user.id,
            name=user.name,
            email=user.email,
            referral_code=user.referral_code,
            joined_at=user.created_at,
            total_referrals=total_referrals,
            total_earnings=float(wallet.available_balance + wallet.locked_balance + wallet.total_withdrawn) if wallet else 0.0,
            pending_earnings=float(wallet.locked_balance) if wallet else 0.0,
            paid_earnings=float(wallet.total_withdrawn) if wallet else 0.0,
            current_commission_rate=current_rate,
            is_enabled=is_enabled,
            custom_rate=custom_rate
        )

    async def update_user_settings(
        self,
        user_id: UUID,
        custom_rate: Optional[float],
        is_enabled: Optional[bool],
        notes: Optional[str]
    ) -> AffiliateSettings:
        """Update affiliate settings for a user"""
        settings = await self.settings_repo.get_or_create(user_id)

        if custom_rate is not None:
            settings.custom_commission_rate = custom_rate
        else:
            settings.custom_commission_rate = None # Reset to default

        if is_enabled is not None:
            settings.is_affiliate_enabled = is_enabled

        if notes is not None:
            settings.notes = notes

        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)

        return settings
