from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

class AffiliateDashboardStats(BaseModel):
    """Overall affiliate program statistics"""
    total_earnings_paid: float
    total_pending_earnings: float
    total_signups: int
    total_referral_volume: float  # Total value of purchases made via referrals
    active_affiliates_count: int  # Users with at least 1 referral
    conversion_rate: float  # Signups / Clicks (if clicks tracked) or just Signups

class AffiliateUserDetail(BaseModel):
    """Detailed stats for a single affiliate"""
    user_id: UUID
    name: str
    email: str
    referral_code: str
    joined_at: datetime

    # Stats
    total_referrals: int
    total_earnings: float
    pending_earnings: float
    paid_earnings: float
    current_commission_rate: float

    # Settings
    is_enabled: bool
    custom_rate: Optional[float]

class AffiliateUserListResponse(BaseModel):
    """Paginated list of affiliates"""
    users: List[AffiliateUserDetail]
    total: int
    page: int
    size: int

class UserCommissionRateUpdate(BaseModel):
    """Update schema for user commission rate"""
    custom_rate: Optional[float]  # None to reset to global default
    is_enabled: Optional[bool]
    notes: Optional[str]

class TopAffiliateItem(BaseModel):
    """Item for top affiliates list"""
    user_id: UUID
    name: str
    referral_code: str
    total_earnings: float
    total_referrals: int

class ProductAffiliateStats(BaseModel):
    """Stats for products/packages sold via affiliates"""
    product_name: str  # e.g. "Standard Pass", "Guaranteed Pass"
    total_sales_count: int
    total_sales_volume: float
    total_commission_generated: float

class GlobalSettingsResponse(BaseModel):
    """Global affiliate settings"""
    default_commission_rate: float
    minimum_withdrawal_amount: float
    is_program_enabled: bool

class GlobalSettingsUpdate(BaseModel):
    """Update global settings"""
    default_commission_rate: Optional[float]
    minimum_withdrawal_amount: Optional[float]
    is_program_enabled: Optional[bool]
