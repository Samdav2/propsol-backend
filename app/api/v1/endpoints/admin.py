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
