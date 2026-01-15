from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.propfirm_registration import PropFirmRegistration, AccountStatus
from app.models.user_purchased_package import UserPurchasedPackage
from app.schema.user import UserCreate, UserRead, UserUpdate
from app.schema.referral import ReferralStatsResponse
from app.schema.user_purchased_package import UserPurchasedPackageRead
from app.service.user_service import UserService
from sqlmodel import select, func
from typing import List

router = APIRouter()

@router.post("", response_model=UserRead)
async def create_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = UserService(session)
    user = await service.get_user_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await service.create_user(user_in, background_tasks)
    return user

@router.get("/me", response_model=UserRead)
async def read_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    return current_user

@router.put("/me", response_model=UserRead)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = UserService(session)
    user = await service.update_user(current_user, user_in)
    return user

@router.get("/referrals", response_model=ReferralStatsResponse)
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    # Get all users referred by current user
    statement = select(User.id).where(User.referred_by == current_user.referral_code)
    result = await session.exec(statement)
    referred_user_ids = result.all()

    if not referred_user_ids:
        return ReferralStatsResponse(
            referral_code=current_user.referral_code,
            total_referrals=0,
            successful_passes=0,
            pending_referrals=0,
            total_earned=0.0
        )

    # Get stats from PropFirmRegistration for these users
    # Successful passes
    pass_stmt = select(func.count(PropFirmRegistration.id)).where(
        PropFirmRegistration.user_id.in_(referred_user_ids),
        PropFirmRegistration.account_status == AccountStatus.passed
    )
    successful_passes = (await session.exec(pass_stmt)).one()

    # Pending referrals (pending registrations)
    pending_stmt = select(func.count(PropFirmRegistration.id)).where(
        PropFirmRegistration.user_id.in_(referred_user_ids),
        PropFirmRegistration.account_status == AccountStatus.pending
    )
    pending_referrals = (await session.exec(pending_stmt)).one()

    # Total earned (2% of account cost for passed accounts)
    earnings_stmt = select(func.sum(PropFirmRegistration.propfirm_account_cost)).where(
        PropFirmRegistration.user_id.in_(referred_user_ids),
        PropFirmRegistration.account_status == AccountStatus.passed
    )
    total_account_cost = (await session.exec(earnings_stmt)).one() or 0.0
    total_earned = total_account_cost * 0.02

    return ReferralStatsResponse(
        referral_code=current_user.referral_code,
        total_referrals=len(referred_user_ids),
        successful_passes=successful_passes,
        pending_referrals=pending_referrals,
        total_earned=total_earned
    )

@router.get("/packages", response_model=List[UserPurchasedPackageRead])
async def get_my_packages(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    statement = select(UserPurchasedPackage).where(UserPurchasedPackage.user_id == current_user.id)
    result = await session.exec(statement)
    return result.all()
