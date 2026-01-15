from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.core import security
from app.db.session import get_session
from app.models.user import User
from app.models.admin import Admin
from app.schema.auth import Token

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    session: AsyncSession = Depends(get_session), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    query = select(User).where(User.email == form_data.username)
    result = await session.exec(query)
    user = result.first()

    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.Status:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "name": user.name,
        "email": user.email,
        "referral_code": user.referral_code
        }


@router.post("/login/admin/access-token", response_model=Token)
async def login_admin_access_token(
    session: AsyncSession = Depends(get_session), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login for admins
    """
    query = select(Admin).where(Admin.email == form_data.username)
    result = await session.exec(query)
    admin = result.first()

    if not admin or not security.verify_password(form_data.password, admin.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not admin.Status:
        raise HTTPException(status_code=400, detail="Inactive admin")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        admin.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "name": admin.name,
        "email": admin.email,
    }

from app.schema.auth import PasswordResetRequest, PasswordResetConfirm
from app.service.user_service import UserService
from app.service.admin_service import AdminService

# User Password Reset
@router.post("/password-recovery/{email}", response_model=dict)
async def recover_password(
    email: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = UserService(session)
    await service.recover_password(email, background_tasks)
    return {"msg": "Password recovery email sent"}

@router.post("/reset-password", response_model=dict)
async def reset_password(
    body: PasswordResetConfirm,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = UserService(session)
    try:
        await service.reset_password(body.token, body.new_password, background_tasks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"msg": "Password updated successfully"}

# Admin Password Reset
@router.post("/admin/password-recovery/{email}", response_model=dict)
async def recover_admin_password(
    email: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = AdminService(session)
    await service.recover_password(email, background_tasks)
    return {"msg": "Password recovery email sent"}

@router.post("/admin/reset-password", response_model=dict)
async def reset_admin_password(
    body: PasswordResetConfirm,
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = AdminService(session)
    try:
        await service.reset_password(body.token, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"msg": "Password updated successfully"}

@router.get("/verify-email", response_model=dict)
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = UserService(session)
    try:
        await service.verify_email(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"msg": "Email verified successfully"}

@router.post("/verify-email/resend", response_model=dict)
async def resend_verification_email(
    email: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = UserService(session)
    user = await service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    await service.send_verification_email(user, background_tasks)
    return {"msg": "Verification email sent"}
