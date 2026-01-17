from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.wallet import Wallet, ReferralEarning, WithdrawalRequest, EarningStatus, WithdrawalStatus
from app.repository.base_repo import BaseRepository


class WalletRepository(BaseRepository[Wallet, dict, dict]):
    """Repository for Wallet operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(Wallet, session)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Wallet]:
        """Get wallet by user ID"""
        query = select(Wallet).where(Wallet.user_id == user_id)
        result = await self.session.exec(query)
        return result.first()

    async def get_or_create(self, user_id: UUID) -> Wallet:
        """Get existing wallet or create new one"""
        wallet = await self.get_by_user_id(user_id)
        if not wallet:
            try:
                wallet = Wallet(
                    user_id=user_id,
                    available_balance=Decimal("0.00"),
                    locked_balance=Decimal("0.00"),
                    total_withdrawn=Decimal("0.00")
                )
                self.session.add(wallet)
                await self.session.commit()
                await self.session.refresh(wallet)
            except Exception:
                # Wallet was created by another request, rollback and fetch
                await self.session.rollback()
                wallet = await self.get_by_user_id(user_id)
        return wallet

    async def update_balances(
        self,
        wallet_id: UUID,
        available_delta: Decimal = Decimal("0"),
        locked_delta: Decimal = Decimal("0"),
        withdrawn_delta: Decimal = Decimal("0")
    ) -> Wallet:
        """Update wallet balances by deltas"""
        wallet = await self.get(wallet_id)
        if wallet:
            wallet.available_balance = Decimal(str(wallet.available_balance)) + available_delta
            wallet.locked_balance = Decimal(str(wallet.locked_balance)) + locked_delta
            wallet.total_withdrawn = Decimal(str(wallet.total_withdrawn)) + withdrawn_delta
            wallet.updated_at = datetime.now(timezone.utc)
            self.session.add(wallet)
            await self.session.commit()
            await self.session.refresh(wallet)
        return wallet


class ReferralEarningRepository(BaseRepository[ReferralEarning, dict, dict]):
    """Repository for ReferralEarning operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(ReferralEarning, session)

    async def get_by_wallet_id(self, wallet_id: UUID) -> List[ReferralEarning]:
        """Get all earnings for a wallet"""
        query = select(ReferralEarning).where(ReferralEarning.wallet_id == wallet_id).order_by(ReferralEarning.created_at.desc())
        result = await self.session.exec(query)
        return result.all()

    async def get_by_referrer_id(self, referrer_id: UUID) -> List[ReferralEarning]:
        """Get all earnings for a referrer"""
        query = select(ReferralEarning).where(ReferralEarning.referrer_id == referrer_id).order_by(ReferralEarning.created_at.desc())
        result = await self.session.exec(query)
        return result.all()

    async def get_by_registration_id(self, registration_id: UUID) -> Optional[ReferralEarning]:
        """Get earning by registration ID"""
        query = select(ReferralEarning).where(ReferralEarning.registration_id == registration_id)
        result = await self.session.exec(query)
        return result.first()

    async def get_locked_earnings(self, wallet_id: UUID) -> List[ReferralEarning]:
        """Get locked earnings for a wallet"""
        query = select(ReferralEarning).where(
            ReferralEarning.wallet_id == wallet_id,
            ReferralEarning.status == EarningStatus.locked
        )
        result = await self.session.exec(query)
        return result.all()

    async def count_by_referrer(self, referrer_id: UUID) -> int:
        """Count total referrals for a referrer"""
        query = select(ReferralEarning).where(ReferralEarning.referrer_id == referrer_id)
        result = await self.session.exec(query)
        return len(result.all())

    async def count_locked_by_wallet(self, wallet_id: UUID) -> int:
        """Count locked earnings for a wallet"""
        query = select(ReferralEarning).where(
            ReferralEarning.wallet_id == wallet_id,
            ReferralEarning.status == EarningStatus.locked
        )
        result = await self.session.exec(query)
        return len(result.all())

    async def release_earning(self, earning_id: UUID) -> Optional[ReferralEarning]:
        """Release a locked earning"""
        earning = await self.get(earning_id)
        if earning and earning.status == EarningStatus.locked:
            earning.status = EarningStatus.released
            earning.challenge_passed = True
            earning.released_at = datetime.now(timezone.utc)
            self.session.add(earning)
            await self.session.commit()
            await self.session.refresh(earning)
        return earning


class WithdrawalRequestRepository(BaseRepository[WithdrawalRequest, dict, dict]):
    """Repository for WithdrawalRequest operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(WithdrawalRequest, session)

    async def get_by_wallet_id(self, wallet_id: UUID) -> List[WithdrawalRequest]:
        """Get all withdrawals for a wallet"""
        query = select(WithdrawalRequest).where(WithdrawalRequest.wallet_id == wallet_id).order_by(WithdrawalRequest.created_at.desc())
        result = await self.session.exec(query)
        return result.all()

    async def get_pending(self) -> List[WithdrawalRequest]:
        """Get all pending withdrawals (for admin)"""
        query = select(WithdrawalRequest).where(WithdrawalRequest.status == WithdrawalStatus.pending).order_by(WithdrawalRequest.created_at.asc())
        result = await self.session.exec(query)
        return result.all()

    async def update_status(
        self,
        withdrawal_id: UUID,
        status: WithdrawalStatus,
        admin_notes: Optional[str] = None
    ) -> Optional[WithdrawalRequest]:
        """Update withdrawal status"""
        withdrawal = await self.get(withdrawal_id)
        if withdrawal:
            withdrawal.status = status
            if admin_notes:
                withdrawal.admin_notes = admin_notes
            if status in [WithdrawalStatus.completed, WithdrawalStatus.rejected]:
                withdrawal.processed_at = datetime.now(timezone.utc)
            self.session.add(withdrawal)
            await self.session.commit()
            await self.session.refresh(withdrawal)
        return withdrawal
