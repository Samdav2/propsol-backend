from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.wallet import (
    Wallet, ReferralEarning, WithdrawalRequest,
    EarningStatus, PaymentMethod, WithdrawalStatus
)
from app.models.propfirm_registration import PassType
from app.repository.wallet_repo import WalletRepository, ReferralEarningRepository, WithdrawalRequestRepository
from app.repository.user_repo import UserRepository
from app.models.user import User
from app.schema.wallet import (
    WalletResponse, WalletSummaryResponse, ReferralEarningResponse,
    WithdrawalCreate, WithdrawalResponse, AdminWithdrawalResponse
)
from app.config import settings

# Commission rate: 2% of purchase
COMMISSION_RATE = Decimal("0.02")
MINIMUM_WITHDRAWAL = Decimal("100.00")


class WalletService:
    """Service for wallet operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallet_repo = WalletRepository(session)
        self.earning_repo = ReferralEarningRepository(session)
        self.withdrawal_repo = WithdrawalRequestRepository(session)
        self.user_repo = UserRepository(User, session)
        # Initialize NOWPayments service lazily or when needed to avoid circular imports if any
        # But here we can just instantiate it when needed.

    async def get_wallet(self, user_id: UUID) -> Wallet:
        """Get or create wallet for user"""
        return await self.wallet_repo.get_or_create(user_id)

    async def get_wallet_summary(self, user_id: UUID) -> WalletSummaryResponse:
        """Get wallet dashboard summary"""
        wallet = await self.get_wallet(user_id)
        total_referrals = await self.earning_repo.count_by_referrer(user_id)
        pending_earnings = await self.earning_repo.count_locked_by_wallet(wallet.id)

        available = float(wallet.available_balance)
        locked = float(wallet.locked_balance)

        return WalletSummaryResponse(
            available_balance=available,
            locked_balance=locked,
            total_balance=available + locked,
            total_withdrawn=float(wallet.total_withdrawn),
            total_referrals=total_referrals,
            pending_earnings=pending_earnings
        )

    async def get_earnings(self, user_id: UUID) -> List[ReferralEarning]:
        """Get all referral earnings for user"""
        wallet = await self.get_wallet(user_id)
        return await self.earning_repo.get_by_wallet_id(wallet.id)

    async def process_referral_purchase(
        self,
        referred_user_id: UUID,
        referrer_code: str,
        pass_type: PassType,
        purchase_amount: Decimal,
        registration_id: Optional[UUID] = None
    ) -> Optional[ReferralEarning]:
        """
        Process referral earnings when a referred user makes a purchase.
        Called by payment processing when payment is confirmed.
        """
        # Find the referrer by their referral code
        referrer = await self.user_repo.get_by_referral_code(referrer_code)
        if not referrer:
            return None

        # Get or create referrer's wallet
        wallet = await self.wallet_repo.get_or_create(referrer.id)

        # Check for custom commission rate
        from app.repository.affiliate_settings_repo import AffiliateSettingsRepository
        from app.repository.global_settings_repo import GlobalSettingsRepository

        settings_repo = AffiliateSettingsRepository(self.session)
        global_repo = GlobalSettingsRepository(self.session)

        user_settings = await settings_repo.get_by_user_id(referrer.id)
        global_settings = await global_repo.get_settings()

        # Check if program is enabled globally
        if not global_settings.is_program_enabled:
            return None

        # Check if affiliate is enabled specifically
        if user_settings and not user_settings.is_affiliate_enabled:
            return None

        # Determine rate
        rate = global_settings.default_commission_rate
        if user_settings and user_settings.custom_commission_rate is not None:
            rate = user_settings.custom_commission_rate

        # Calculate commission
        commission = purchase_amount * rate

        # Determine status based on pass type
        if pass_type == PassType.standard_pass:
            status = EarningStatus.available
            # Add to available balance immediately
            await self.wallet_repo.update_balances(
                wallet.id,
                available_delta=commission
            )
        else:
            # Guaranteed pass - lock until challenge passed
            status = EarningStatus.locked
            # Add to locked balance
            await self.wallet_repo.update_balances(
                wallet.id,
                locked_delta=commission
            )

        # Create earning record
        earning = ReferralEarning(
            wallet_id=wallet.id,
            referrer_id=referrer.id,
            referred_user_id=referred_user_id,
            registration_id=registration_id,
            pass_type=pass_type.value,
            amount=commission,
            status=status,
            challenge_passed=(pass_type == PassType.standard_pass)  # Standard pass doesn't need challenge
        )
        self.session.add(earning)
        await self.session.commit()
        await self.session.refresh(earning)

        return earning

    async def unlock_earning(self, earning_id: UUID, user_id: UUID) -> Optional[ReferralEarning]:
        """
        Unlock a guaranteed pass earning after challenge is passed.
        Called when admin marks challenge as passed.
        """
        earning = await self.earning_repo.get(earning_id)
        if not earning or earning.status != EarningStatus.locked:
            return None

        # Verify the earning belongs to the user's wallet
        wallet = await self.wallet_repo.get_by_user_id(user_id)
        if not wallet or earning.wallet_id != wallet.id:
            return None

        # Release the earning
        earning = await self.earning_repo.release_earning(earning_id)
        if earning:
            # Move from locked to available balance
            await self.wallet_repo.update_balances(
                wallet.id,
                available_delta=Decimal(str(earning.amount)),
                locked_delta=-Decimal(str(earning.amount))
            )

        return earning

    async def release_earnings_by_registration(self, registration_id: UUID) -> Optional[ReferralEarning]:
        """
        Release locked earnings when a challenge is passed.
        Called by admin service when updating account_status to 'passed'.
        """
        earning = await self.earning_repo.get_by_registration_id(registration_id)
        if not earning or earning.status != EarningStatus.locked:
            return None

        # Get wallet
        wallet = await self.wallet_repo.get(earning.wallet_id)
        if not wallet:
            return None

        # Release the earning
        earning = await self.earning_repo.release_earning(earning.id)
        if earning:
            # Move from locked to available balance
            await self.wallet_repo.update_balances(
                wallet.id,
                available_delta=Decimal(str(earning.amount)),
                locked_delta=-Decimal(str(earning.amount))
            )

        return earning

    async def request_withdrawal(
        self,
        user_id: UUID,
        withdrawal_data: WithdrawalCreate,
        background_tasks: BackgroundTasks
    ) -> WithdrawalRequest:
        """Create a withdrawal request"""
        wallet = await self.get_wallet(user_id)
        amount = Decimal(str(withdrawal_data.amount))

        # Check minimum withdrawal
        if amount < MINIMUM_WITHDRAWAL:
            raise ValueError(f"Minimum withdrawal amount is ${MINIMUM_WITHDRAWAL}")

        # Check available balance
        if amount > wallet.available_balance:
            raise ValueError("Insufficient available balance")

        # Validate crypto address if applicable
        if withdrawal_data.payment_method == PaymentMethod.crypto and withdrawal_data.crypto_details:
            from app.service.nowpayments_service import NOWPaymentsService
            now_service = NOWPaymentsService()
            is_valid = await now_service.validate_address(
                address=withdrawal_data.crypto_details.wallet_address,
                currency=withdrawal_data.crypto_details.currency
            )
            if not is_valid:
                raise ValueError(f"Invalid {withdrawal_data.crypto_details.currency} address")

        # Build withdrawal request
        withdrawal = WithdrawalRequest(
            wallet_id=wallet.id,
            amount=amount,
            payment_method=withdrawal_data.payment_method,
            status=WithdrawalStatus.pending
        )

        # Set payment method specific details
        if withdrawal_data.payment_method == PaymentMethod.bank_transfer and withdrawal_data.bank_details:
            withdrawal.bank_name = withdrawal_data.bank_details.bank_name
            withdrawal.account_number = withdrawal_data.bank_details.account_number
            withdrawal.account_name = withdrawal_data.bank_details.account_name
            withdrawal.routing_number = withdrawal_data.bank_details.routing_number
            withdrawal.swift_code = withdrawal_data.bank_details.swift_code
        elif withdrawal_data.payment_method == PaymentMethod.crypto and withdrawal_data.crypto_details:
            withdrawal.crypto_wallet_address = withdrawal_data.crypto_details.wallet_address
            withdrawal.crypto_network = withdrawal_data.crypto_details.network
            withdrawal.crypto_currency = withdrawal_data.crypto_details.currency
        elif withdrawal_data.payment_method == PaymentMethod.paypal and withdrawal_data.paypal_details:
            withdrawal.paypal_email = withdrawal_data.paypal_details.email

        self.session.add(withdrawal)

        # Deduct from available balance (pending withdrawal)
        await self.wallet_repo.update_balances(
            wallet.id,
            available_delta=-amount
        )

        # Store ID before commit expires the object
        withdrawal_id = withdrawal.id

        await self.session.commit()

        # Re-fetch to avoid MissingGreenlet/InvalidRequestError with session.refresh
        withdrawal = await self.withdrawal_repo.get(withdrawal_id)

        # Send notification emails
        user = await self.user_repo.get(user_id)
        if user:
            from app.service.mail import send_email
            from app.config import settings

            # Notify user
            background_tasks.add_task(
                send_email,
                email_to=user.email,
                subject="Withdrawal Request Received",
                template_name="withdrawal_request.html",
                context={
                    "name": user.name,
                    "amount": float(amount),
                    "payment_method": withdrawal_data.payment_method.value,
                    "created_at": withdrawal.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            )

            # Notify admin
            if settings.ADMIN_EMAIL:
                background_tasks.add_task(
                    send_email,
                    email_to=settings.ADMIN_EMAIL,
                    subject="New Withdrawal Request",
                    template_name="admin_withdrawal_request.html",
                    context={
                        "user_name": user.name,
                        "user_email": user.email,
                        "amount": float(amount),
                        "payment_method": withdrawal_data.payment_method.value,
                        "created_at": withdrawal.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    }
                )

        return withdrawal

    async def get_withdrawals(self, user_id: UUID) -> List[WithdrawalRequest]:
        """Get all withdrawals for user"""
        wallet = await self.get_wallet(user_id)
        return await self.withdrawal_repo.get_by_wallet_id(wallet.id)

    async def update_withdrawal_status(
        self,
        withdrawal_id: UUID,
        status: WithdrawalStatus,
        admin_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Optional[WithdrawalRequest]:
        """Update withdrawal status (admin action)"""
        withdrawal = await self.withdrawal_repo.get(withdrawal_id)
        if not withdrawal:
            return None

        old_status = withdrawal.status
        withdrawal = await self.withdrawal_repo.update_status(
            withdrawal_id=withdrawal_id,
            status=status,
            admin_notes=admin_notes,
            rejection_reason=rejection_reason
        )

        if withdrawal:
            wallet = await self.wallet_repo.get(withdrawal.wallet_id)

            if status == WithdrawalStatus.completed:
                # Add to total withdrawn
                await self.wallet_repo.update_balances(
                    wallet.id,
                    withdrawn_delta=Decimal(str(withdrawal.amount))
                )
            elif status == WithdrawalStatus.rejected and old_status == WithdrawalStatus.pending:
                # Refund to available balance
                await self.wallet_repo.update_balances(
                    wallet.id,
                    available_delta=Decimal(str(withdrawal.amount))
                )

            # Send notification if background_tasks provided
            if background_tasks and wallet:
                # Get user from wallet
                user = await self.user_repo.get(wallet.user_id)
                if user:
                    from app.service.mail import send_email

                    email_context = {
                        "name": user.name,
                        "amount": float(withdrawal.amount),
                        "status": status.value,
                        "payment_method": withdrawal.payment_method.value,
                        "admin_notes": admin_notes or ""
                    }

                    if rejection_reason:
                        email_context["rejection_reason"] = rejection_reason

                    background_tasks.add_task(
                        send_email,
                        email_to=user.email,
                        subject=f"Withdrawal {status.value.capitalize()}",
                        template_name="withdrawal_completed.html",
                        context=email_context
                    )

        return withdrawal

    async def get_pending_withdrawals(self) -> List[WithdrawalRequest]:
        """Get all pending withdrawals (for admin)"""
        return await self.withdrawal_repo.get_pending()

    async def get_all_withdrawals(self, status: Optional[str] = None, limit: int = 10, offset: int = 0) -> dict:
        """Get all withdrawals with optional status filter"""
        results, total = await self.withdrawal_repo.get_all_with_filters(status=status, limit=limit, offset=offset)

        withdrawals = []
        for w, user in results:
            withdrawals.append(
                AdminWithdrawalResponse(
                    id=w.id,
                    wallet_id=w.wallet_id,
                    amount=float(w.amount),
                    payment_method=w.payment_method,
                    status=w.status,
                    bank_name=w.bank_name,
                    account_number=w.account_number,
                    account_name=w.account_name,
                    crypto_wallet_address=w.crypto_wallet_address,
                    crypto_network=w.crypto_network,
                    crypto_currency=w.crypto_currency,
                    paypal_email=w.paypal_email,
                    admin_notes=w.admin_notes,
                    rejection_reason=w.rejection_reason,
                    created_at=w.created_at,
                    processed_at=w.processed_at,
                    user_name=user.name,
                    user_email=user.email
                )
            )

        return {
            "withdrawals": withdrawals,
            "total_count": total
        }

    async def initiate_nowpayments_payout(self, withdrawal_id: UUID) -> WithdrawalRequest:
        """Initiate a payout via NOWPayments"""
        withdrawal = await self.withdrawal_repo.get(withdrawal_id)
        if not withdrawal:
            raise ValueError("Withdrawal request not found")

        if withdrawal.status != WithdrawalStatus.pending:
            raise ValueError("Withdrawal request is not pending")

        # Create payout in NOWPayments
        withdrawals_payload = [{
            "address": withdrawal.crypto_wallet_address,
            "currency": withdrawal.crypto_currency,
            "amount": float(withdrawal.amount),
            "ipn_callback_url": settings.NOWPAYMENTS_IPN_CALLBACK_URL,
            "extra_id": str(withdrawal.id) # Use withdrawal ID as extra_id for tracking
        }]

        try:
            from app.service.nowpayments_service import NOWPaymentsService
            now_service = NOWPaymentsService()

            response = await now_service.create_payout(
                withdrawals=withdrawals_payload,
                payout_description=f"Withdrawal {withdrawal.id}"
            )

            # Update withdrawal with batch ID
            withdrawal.batch_withdrawal_id = str(response.get("id"))

            # Assuming single withdrawal in batch, get the payout ID
            if response.get("withdrawals"):
                withdrawal.payout_id = str(response["withdrawals"][0].get("id"))
                withdrawal.external_status = response["withdrawals"][0].get("status")

            # Save changes
            self.session.add(withdrawal)

            # Store ID before commit
            withdrawal_id = withdrawal.id

            await self.session.commit()

            # Re-fetch to avoid MissingGreenlet/InvalidRequestError with session.refresh
            withdrawal = await self.withdrawal_repo.get(withdrawal_id)

            return withdrawal

        except Exception as e:
            raise ValueError(f"Failed to initiate payout: {str(e)}")

    async def verify_nowpayments_payout(self, batch_id: str, verification_code: str) -> bool:
        """Verify a payout batch"""
        from app.service.nowpayments_service import NOWPaymentsService
        now_service = NOWPaymentsService()
        return await now_service.verify_payout(batch_id, verification_code)



# Helper function to be called from payment flow
async def process_referral_purchase(
    db: AsyncSession,
    referred_user_id: UUID,
    referrer_code: str,
    pass_type: PassType,
    purchase_amount: Decimal,
    registration_id: Optional[UUID] = None
) -> Optional[ReferralEarning]:
    """Convenience function to process referral from payment flow"""
    service = WalletService(db)
    return await service.process_referral_purchase(
        referred_user_id=referred_user_id,
        referrer_code=referrer_code,
        pass_type=pass_type,
        purchase_amount=purchase_amount,
        registration_id=registration_id
    )
