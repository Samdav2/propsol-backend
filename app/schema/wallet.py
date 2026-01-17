from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator

from app.models.wallet import EarningStatus, PaymentMethod, WithdrawalStatus


# --- Wallet Response Schemas ---

class WalletResponse(BaseModel):
    """Wallet balance response"""
    id: UUID
    user_id: UUID
    available_balance: float
    locked_balance: float
    total_withdrawn: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletSummaryResponse(BaseModel):
    """Dashboard wallet summary"""
    available_balance: float
    locked_balance: float
    total_balance: float
    total_withdrawn: float
    total_referrals: int
    pending_earnings: int  # Locked earnings count


# --- Referral Earning Schemas ---

class ReferralEarningResponse(BaseModel):
    """Individual referral earning details"""
    id: UUID
    referrer_id: UUID
    referred_user_id: UUID
    registration_id: Optional[UUID]
    pass_type: str
    amount: float
    status: EarningStatus
    challenge_passed: bool
    created_at: datetime
    released_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReferralEarningsListResponse(BaseModel):
    """List of referral earnings"""
    earnings: List[ReferralEarningResponse]
    total_count: int


class UnlockEarningRequest(BaseModel):
    """Request to unlock a guaranteed pass earning"""
    earning_id: UUID


# --- Withdrawal Schemas ---

class BankDetails(BaseModel):
    """Bank transfer details"""
    bank_name: str
    account_number: str
    account_name: str
    routing_number: Optional[str] = None
    swift_code: Optional[str] = None


class CryptoDetails(BaseModel):
    """Cryptocurrency withdrawal details"""
    wallet_address: str
    network: str  # e.g., "ERC20", "TRC20", "BTC"
    currency: str  # e.g., "USDT", "BTC", "ETH"


class PayPalDetails(BaseModel):
    """PayPal withdrawal details"""
    email: EmailStr


class WithdrawalCreate(BaseModel):
    """Create withdrawal request"""
    amount: float
    payment_method: PaymentMethod
    bank_details: Optional[BankDetails] = None
    crypto_details: Optional[CryptoDetails] = None
    paypal_details: Optional[PayPalDetails] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v < 100:
            raise ValueError('Minimum withdrawal amount is $100')
        return v


class WithdrawalResponse(BaseModel):
    """Withdrawal request response"""
    id: UUID
    wallet_id: UUID
    amount: float
    payment_method: PaymentMethod
    status: WithdrawalStatus
    bank_name: Optional[str]
    account_number: Optional[str]
    account_name: Optional[str]
    crypto_wallet_address: Optional[str]
    crypto_network: Optional[str]
    crypto_currency: Optional[str]
    paypal_email: Optional[str]
    admin_notes: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class WithdrawalListResponse(BaseModel):
    """List of withdrawals"""
    withdrawals: List[WithdrawalResponse]
    total_count: int


class WithdrawalStatusUpdate(BaseModel):
    """Admin update withdrawal status"""
    status: WithdrawalStatus
    admin_notes: Optional[str] = None
