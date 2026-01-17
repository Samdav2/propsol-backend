from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
from app.schema.affiliate_admin import (
    AffiliateDashboardStats, AffiliateUserDetail, TopAffiliateItem,
    ProductAffiliateStats, UserCommissionRateUpdate, AffiliateUserListResponse,
    GlobalSettingsResponse, GlobalSettingsUpdate
)
from app.service.affiliate_admin_service import AffiliateAdminService

router = APIRouter()

@router.get("/dashboard", response_model=AffiliateDashboardStats)
async def get_dashboard_stats(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Get overall affiliate program statistics"""
    service = AffiliateAdminService(session)
    return await service.get_dashboard_stats()

@router.get("/top", response_model=List[TopAffiliateItem])
async def get_top_affiliates(
    limit: int = Query(10, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Get top performing affiliates"""
    service = AffiliateAdminService(session)
    return await service.get_top_affiliates(limit)

@router.get("/products", response_model=List[ProductAffiliateStats])
async def get_product_stats(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Get affiliate stats by product/package"""
    service = AffiliateAdminService(session)
    return await service.get_product_stats()

@router.get("/settings/global", response_model=GlobalSettingsResponse)
async def get_global_settings(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Get global affiliate settings"""
    service = AffiliateAdminService(session)
    return await service.get_global_settings()

@router.patch("/settings/global", response_model=GlobalSettingsResponse)
async def update_global_settings(
    settings: GlobalSettingsUpdate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Update global affiliate settings"""
    service = AffiliateAdminService(session)
    return await service.update_global_settings(
        default_commission_rate=settings.default_commission_rate,
        minimum_withdrawal_amount=settings.minimum_withdrawal_amount,
        is_program_enabled=settings.is_program_enabled
    )

@router.get("/users/{user_id}", response_model=AffiliateUserDetail)
async def get_affiliate_detail(
    user_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Get detailed stats for a specific affiliate"""
    service = AffiliateAdminService(session)
    detail = await service.get_affiliate_detail(user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="User not found")
    return detail

@router.patch("/users/{user_id}/settings")
async def update_user_settings(
    user_id: UUID,
    settings: UserCommissionRateUpdate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """Update affiliate settings for a user (commission rate, enabled status)"""
    service = AffiliateAdminService(session)
    # Verify user exists first
    detail = await service.get_affiliate_detail(user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="User not found")

    updated_settings = await service.update_user_settings(
        user_id=user_id,
        custom_rate=settings.custom_rate,
        is_enabled=settings.is_enabled,
        notes=settings.notes
    )
    return {"message": "Settings updated successfully"}
