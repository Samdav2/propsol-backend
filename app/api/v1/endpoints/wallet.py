from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_user, get_current_admin
from app.models.user import User
from app.models.admin import Admin
from app.models.wallet import WithdrawalStatus
from app.service.wallet_service import WalletService
from app.schema.wallet import (
    WalletResponse, WalletSummaryResponse, ReferralEarningResponse,
    ReferralEarningsListResponse, WithdrawalCreate, WithdrawalResponse,
    WithdrawalListResponse, WithdrawalStatusUpdate, UnlockEarningRequest
)

router = APIRouter()


@router.get("", response_model=WalletResponse)
async def get_wallet(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get user's wallet balance"""
    service = WalletService(db)
    wallet = await service.get_wallet(current_user.id)
    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        available_balance=float(wallet.available_balance),
        locked_balance=float(wallet.locked_balance),
        total_withdrawn=float(wallet.total_withdrawn),
        created_at=wallet.created_at,
        updated_at=wallet.updated_at
    )


@router.get("/summary", response_model=WalletSummaryResponse)
async def get_wallet_summary(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get wallet dashboard summary with referral stats"""
    service = WalletService(db)
    return await service.get_wallet_summary(current_user.id)


@router.get("/earnings", response_model=ReferralEarningsListResponse)
async def get_referral_earnings(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get list of referral earnings"""
    service = WalletService(db)
    earnings = await service.get_earnings(current_user.id)

    return ReferralEarningsListResponse(
        earnings=[
            ReferralEarningResponse(
                id=e.id,
                referrer_id=e.referrer_id,
                referred_user_id=e.referred_user_id,
                registration_id=e.registration_id,
                pass_type=e.pass_type,
                amount=float(e.amount),
                status=e.status,
                challenge_passed=e.challenge_passed,
                created_at=e.created_at,
                released_at=e.released_at
            ) for e in earnings
        ],
        total_count=len(earnings)
    )


@router.post("/earnings/unlock", response_model=ReferralEarningResponse)
async def unlock_earning(
    request: UnlockEarningRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Unlock a locked guaranteed pass earning (when challenge is passed)"""
    service = WalletService(db)
    earning = await service.unlock_earning(request.earning_id, current_user.id)

    if not earning:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Earning not found or already unlocked"
        )

    return ReferralEarningResponse(
        id=earning.id,
        referrer_id=earning.referrer_id,
        referred_user_id=earning.referred_user_id,
        registration_id=earning.registration_id,
        pass_type=earning.pass_type,
        amount=float(earning.amount),
        status=earning.status,
        challenge_passed=earning.challenge_passed,
        created_at=earning.created_at,
        released_at=earning.released_at
    )


@router.post("/withdraw", response_model=WithdrawalResponse)
async def request_withdrawal(
    withdrawal_data: WithdrawalCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Request a withdrawal (minimum $100)"""
    service = WalletService(db)

    try:
        withdrawal = await service.request_withdrawal(
            user_id=current_user.id,
            withdrawal_data=withdrawal_data,
            background_tasks=background_tasks
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return WithdrawalResponse(
        id=withdrawal.id,
        wallet_id=withdrawal.wallet_id,
        amount=float(withdrawal.amount),
        payment_method=withdrawal.payment_method,
        status=withdrawal.status,
        bank_name=withdrawal.bank_name,
        account_number=withdrawal.account_number,
        account_name=withdrawal.account_name,
        crypto_wallet_address=withdrawal.crypto_wallet_address,
        crypto_network=withdrawal.crypto_network,
        crypto_currency=withdrawal.crypto_currency,
        paypal_email=withdrawal.paypal_email,
        admin_notes=withdrawal.admin_notes,
        created_at=withdrawal.created_at,
        processed_at=withdrawal.processed_at
    )


@router.get("/withdrawals", response_model=WithdrawalListResponse)
async def get_withdrawals(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get user's withdrawal history"""
    service = WalletService(db)
    withdrawals = await service.get_withdrawals(current_user.id)

    return WithdrawalListResponse(
        withdrawals=[
            WithdrawalResponse(
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
                created_at=w.created_at,
                processed_at=w.processed_at
            ) for w in withdrawals
        ],
        total_count=len(withdrawals)
    )


@router.patch("/withdrawals/{withdrawal_id}", response_model=WithdrawalResponse)
async def update_withdrawal_status(
    withdrawal_id: UUID,
    status_update: WithdrawalStatusUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update withdrawal status (admin only)"""
    service = WalletService(db)
    withdrawal = await service.update_withdrawal_status(
        withdrawal_id=withdrawal_id,
        status=status_update.status,
        admin_notes=status_update.admin_notes,
        background_tasks=background_tasks
    )

    if not withdrawal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Withdrawal not found"
        )

    return WithdrawalResponse(
        id=withdrawal.id,
        wallet_id=withdrawal.wallet_id,
        amount=float(withdrawal.amount),
        payment_method=withdrawal.payment_method,
        status=withdrawal.status,
        bank_name=withdrawal.bank_name,
        account_number=withdrawal.account_number,
        account_name=withdrawal.account_name,
        crypto_wallet_address=withdrawal.crypto_wallet_address,
        crypto_network=withdrawal.crypto_network,
        crypto_currency=withdrawal.crypto_currency,
        paypal_email=withdrawal.paypal_email,
        admin_notes=withdrawal.admin_notes,
        created_at=withdrawal.created_at,
        processed_at=withdrawal.processed_at
    )


@router.get("/admin/withdrawals/pending", response_model=WithdrawalListResponse)
async def get_pending_withdrawals(
    db: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all pending withdrawals (admin only)"""
    service = WalletService(db)
    withdrawals = await service.get_pending_withdrawals()

    return WithdrawalListResponse(
        withdrawals=[
            WithdrawalResponse(
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
                created_at=w.created_at,
                processed_at=w.processed_at
            ) for w in withdrawals
        ],
        total_count=len(withdrawals)
    )
