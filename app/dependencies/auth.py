import uuid
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.core import security
from app.db.session import get_session
from app.models.user import User
from app.models.admin import Admin
from app.schema.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login/access-token")
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login/admin/access-token")


async def get_current_user(
    session: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    # Use selectinload for relationships as requested
    query = select(User).where(User.id == uuid.UUID(token_data.sub)).options(
        selectinload(User.payments),
        selectinload(User.user_discounts),
        selectinload(User.transactions),
        selectinload(User.prop_firm_registrations)
    )
    result = await session.exec(query)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.Status: # Assuming Status is boolean True for active
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_admin(
    session: AsyncSession = Depends(get_session), token: str = Depends(admin_oauth2_scheme)
) -> Admin:
    try:
        payload = jwt.decode(
            token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    query = select(Admin).where(Admin.id == uuid.UUID(token_data.sub))
    result = await session.exec(query)
    admin = result.first()

    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin
