from pydantic import BaseModel

class ReferralStatsResponse(BaseModel):
    referral_code: str
    total_referrals: int
    successful_passes: int
    pending_referrals: int
    total_earned: float
