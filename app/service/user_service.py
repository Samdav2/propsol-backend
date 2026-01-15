from uuid import UUID
from typing import Optional
from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User
from app.schema.user import UserCreate, UserUpdate
from app.repository.user_repo import UserRepository
from app.core.security import get_password_hash

class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(User, session)

    async def create_user(self, user_in: UserCreate, background_tasks: BackgroundTasks) -> User:
        user_data = user_in.dict()
        user_data["password"] = get_password_hash(user_in.password)
        # Handle referral code generation logic if needed, but model handles default factory
        # Handle referred_by if needed
        user = await self.repo.create(user_data)

        # Notify Admin
        from app.service.mail import send_email
        from app.config import settings
        if settings.ADMIN_EMAIL:
            background_tasks.add_task(
                send_email,
                email_to=settings.ADMIN_EMAIL,
                subject="New User Registration",
                template_name="admin_new_user.html",
                context={
                    "name": user.name,
                    "email": user.email,
                    "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            )

        # Notify Referrer
        if user.referred_by:
            referrer = await self.repo.get_by_referral_code(user.referred_by)
            if referrer:
                background_tasks.add_task(
                    send_email,
                    email_to=referrer.email,
                    subject="New Referral Signup!",
                    template_name="referral_signup.html",
                    context={
                        "referrer_name": referrer.name,
                        "new_user_name": user.name
                    }
                )

        # Send Verification Email
        await self.send_verification_email(user, background_tasks)

        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.repo.get_by_email(email)

    async def get_user(self, user_id: UUID) -> Optional[User]:
        return await self.repo.get(user_id)

    async def update_user(self, user: User, user_in: UserUpdate) -> User:
        return await self.repo.update(db_obj=user, obj_in=user_in)

    async def recover_password(self, email: str, background_tasks: BackgroundTasks) -> None:
        user = await self.get_user_by_email(email)
        if not user:
            # Do not reveal if user exists
            return

        # Generate reset token (valid for 1 hour)
        from app.core.security import create_access_token
        from datetime import timedelta
        reset_token = create_access_token(user.id, expires_delta=timedelta(hours=1))

        # Send email
        from app.service.mail import send_email
        reset_link = f"https://propsol-frontend.vercel.app/reset-password?token={reset_token}"
        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject="Password Reset Request",
            template_name="reset_password.html",
            context={"name": user.name, "reset_link": reset_link}
        )

    async def reset_password(self, token: str, new_password: str, background_tasks: BackgroundTasks) -> None:
        from app.core.security import get_password_hash
        from jose import jwt, JWTError
        from app.config import settings

        try:
            payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token")
        except JWTError:
            raise ValueError("Invalid token")

        user = await self.get_user(UUID(user_id))
        if not user:
            raise ValueError("User not found")

        hashed_password = get_password_hash(new_password)
        user.password = hashed_password
        self.repo.session.add(user)
        await self.repo.session.commit()

        # Notify User via Email
        from app.service.mail import send_email
        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject="Password Changed Successfully",
            template_name="password_changed.html",
            context={"name": user.name}
        )

        # Create notification for password change
        from app.service.notification_service import NotificationService
        notification_service = NotificationService(self.repo.session)
        await notification_service.create_password_changed_notification(user.id)

    async def send_verification_email(self, user: User, background_tasks: BackgroundTasks) -> None:
        from app.core.security import create_access_token
        from datetime import timedelta
        from app.service.mail import send_email

        # Token valid for 24 hours
        verification_token = create_access_token(user.id, expires_delta=timedelta(hours=24))
        verification_link = f"https://propsol-frontend.vercel.app/verify-email?token={verification_token}"

        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject="Verify Your Email",
            template_name="verify_email.html",
            context={"name": user.name, "verification_link": verification_link}
        )

    async def verify_email(self, token: str) -> None:
        from jose import jwt, JWTError
        from app.config import settings

        try:
            payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token")
        except JWTError:
            raise ValueError("Invalid token")

        user = await self.get_user(UUID(user_id))
        if not user:
            raise ValueError("User not found")

        if user.email_verified:
            return # Already verified

        user.email_verified = True
        self.repo.session.add(user)
        await self.repo.session.commit()

        # Create notification for email verification
        from app.service.notification_service import NotificationService
        notification_service = NotificationService(self.repo.session)
        await notification_service.create_email_verified_notification(user.id)
