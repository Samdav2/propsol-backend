from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
from app.models.user_purchased_package import UserPurchasedPackage
from app.schema.admin import AdminCreate, AdminRead, AdminUpdate
from app.schema.user import UserRead, UserUpdate
from app.schema.transactions import TransactionRead
from app.schema.user_purchased_package import UserPurchasedPackageCreate, UserPurchasedPackageRead
from app.schema.wallet import WithdrawalStatusUpdate, AdminWithdrawalListResponse

from app.service.admin_service import AdminService
from app.schema.propfirm_registration import PropFirmRegistrationRead, PropFirmRegistrationUpdate
from app.service.propfirm_registration_service import PropFirmRegistrationService
from uuid import UUID
from app.service.mail import send_email
from app.models.user import User

router = APIRouter()


@router.post("", response_model=AdminRead)
async def create_admin(
    admin_in: AdminCreate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Create new admin.
    """
    service = AdminService(session)
    admin = await service.get_admin_by_email(admin_in.email)
    if admin:
        raise HTTPException(
            status_code=400,
            detail="The admin with this email already exists in the system.",
        )
    admin = await service.create_admin(admin_in)
    return admin


@router.get("/me", response_model=AdminRead)
async def read_admin_me(
    current_admin: Admin = Depends(get_current_admin),
) -> Any:
    """
    Get current admin.
    """
    return current_admin


@router.get("/stats", response_model=dict)
async def read_stats(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = AdminService(session)
    return await service.get_stats()

@router.get("/users", response_model=List[UserRead])
async def read_users(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = AdminService(session)
    users = await service.get_all_users()
    return users


@router.get("/transactions", response_model=List[TransactionRead])
async def read_transactions(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = AdminService(session)
    return await service.get_all_transactions()


@router.get("/prop-firms", response_model=List[PropFirmRegistrationRead])
async def read_prop_firms(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = AdminService(session)
    return await service.get_all_prop_firm_registrations()


@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = AdminService(session)
    user = await service.update_user(user_id, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/prop-firm/{registration_id}", response_model=PropFirmRegistrationRead)
async def update_propfirm_registration(
    registration_id: UUID,
    registration_in: PropFirmRegistrationUpdate,
    background_tasks: BackgroundTasks,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = PropFirmRegistrationService(session)
    registration = await service.update_registration(registration_id, registration_in, background_tasks)
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    return registration

@router.post("/packages", response_model=UserPurchasedPackageRead)
async def assign_package_to_user(
    package_in: UserPurchasedPackageCreate,
    background_tasks: BackgroundTasks,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    package = UserPurchasedPackage.from_orm(package_in)
    session.add(package)
    await session.commit()
    await session.refresh(package)

    user = await session.get(User, package.user_id)
    if user:
        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject="Package Purchased Successfully",
            template_name="user_package_purchased.html",
            context={
                "name": user.name,
                "package_name": package.package_name,
                "price": package.price,
                "date": package.created_at.strftime("%Y-%m-%d")
            }
        )

    return package


@router.get("/withdrawals", response_model=AdminWithdrawalListResponse)
async def list_all_withdrawals(
    status: str = None,
    limit: int = 10,
    page: int = 0,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    List all withdrawals with optional status filter.
    """
    from app.service.wallet_service import WalletService
    service = WalletService(session)
    return await service.get_all_withdrawals(status=status, limit=limit, offset=page * limit)


@router.patch("/withdrawals/{withdrawal_id}", response_model=Any)
async def update_withdrawal_status(
    withdrawal_id: UUID,
    status_update: WithdrawalStatusUpdate,
    background_tasks: BackgroundTasks,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Update withdrawal status (admin only).
    """
    from app.service.wallet_service import WalletService

    service = WalletService(session)

    withdrawal = await service.update_withdrawal_status(
        withdrawal_id=withdrawal_id,
        status=status_update.status,
        admin_notes=status_update.admin_notes,
        rejection_reason=status_update.rejection_reason,
        background_tasks=background_tasks
    )

    if not withdrawal:
        raise HTTPException(
            status_code=404,
            detail="Withdrawal not found"
        )

    return withdrawal


@router.post("/withdrawals/{withdrawal_id}/approve", response_model=dict)
async def approve_withdrawal_payout(
    withdrawal_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Approve a withdrawal and initiate NOWPayments payout.
    """
    from app.service.wallet_service import WalletService
    service = WalletService(session)
    try:
        withdrawal = await service.initiate_nowpayments_payout(withdrawal_id)
        return {
            "message": "Payout initiated successfully",
            "batch_withdrawal_id": withdrawal.batch_withdrawal_id,
            "payout_id": withdrawal.payout_id,
            "status": withdrawal.external_status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/withdrawals/verify", response_model=dict)
async def verify_withdrawal_payout(
    batch_id: str,
    verification_code: str,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Verify a NOWPayments payout batch with 2FA code.
    """
    from app.service.wallet_service import WalletService
    service = WalletService(session)
    is_verified = await service.verify_nowpayments_payout(batch_id, verification_code)

    if is_verified:
        return {"message": "Payout verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Verification failed")


@router.get("/withdrawals/nowpayments", response_model=dict)
async def list_nowpayments_payouts(
    limit: int = 10,
    page: int = 0,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    List payouts directly from NOWPayments.
    """
    from app.service.nowpayments_service import NOWPaymentsService
    now_service = NOWPaymentsService()
    return await now_service.get_payouts({"limit": limit, "page": page})
