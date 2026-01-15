from uuid import UUID
from typing import Optional, List
from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.admin import Admin
from app.models.user import User
from app.schema.admin import AdminCreate, AdminUpdate
from app.repository.admin_repo import AdminRepository
from app.repository.user_repo import UserRepository
from app.repository.transactions_repo import TransactionRepository
from app.repository.propfirm_registration_repo import PropFirmRegistrationRepository
from app.models.transactions import Transaction
from app.models.propfirm_registration import PropFirmRegistration
from app.schema.user import UserUpdate
from app.core.security import get_password_hash

class AdminService:
    def __init__(self, session: AsyncSession):
        self.repo = AdminRepository(Admin, session)
        self.user_repo = UserRepository(User, session)
        self.transaction_repo = TransactionRepository(Transaction, session)
        self.prop_firm_repo = PropFirmRegistrationRepository(PropFirmRegistration, session)

    async def create_admin(self, admin_in: AdminCreate) -> Admin:
        admin_data = admin_in.dict()
        admin_data["password"] = get_password_hash(admin_in.password)
        return await self.repo.create(admin_data)

    async def get_admin_by_email(self, email: str) -> Optional[Admin]:
        return await self.repo.get_by_email(email)

    async def get_admin(self, admin_id: UUID) -> Optional[Admin]:
        return await self.repo.get(admin_id)

    async def get_all_users(self) -> List[User]:
        return await self.user_repo.get_all()

    async def get_all_transactions(self) -> List[Transaction]:
        return await self.transaction_repo.get_all()

    async def get_all_prop_firm_registrations(self) -> List[PropFirmRegistration]:
        return await self.prop_firm_repo.get_all()

    async def update_user(self, user_id: UUID, user_in: UserUpdate) -> Optional[User]:
        user = await self.user_repo.get(user_id)
        if not user:
            return None
        return await self.user_repo.update(db_obj=user, obj_in=user_in)

    async def recover_password(self, email: str, background_tasks: BackgroundTasks) -> None:
        admin = await self.get_admin_by_email(email)
        if not admin:
            return

        from app.core.security import create_access_token
        from datetime import timedelta
        reset_token = create_access_token(admin.id, expires_delta=timedelta(hours=1))

        from app.service.mail import send_email
        reset_link = f"https://propsol-frontend.vercel.app/reset-password?token={reset_token}"
        background_tasks.add_task(
            send_email,
            email_to=admin.email,
            subject="Admin Password Reset Request",
            template_name="reset_password.html",
            context={"name": admin.name, "reset_link": reset_link}
        )

    async def reset_password(self, token: str, new_password: str) -> None:
        from app.core.security import get_password_hash
        from jose import jwt, JWTError
        from app.config import settings

        try:
            payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
            admin_id = payload.get("sub")
            if not admin_id:
                raise ValueError("Invalid token")
        except JWTError:
            raise ValueError("Invalid token")

        admin = await self.get_admin(UUID(admin_id))
        if not admin:
            raise ValueError("Admin not found")

        hashed_password = get_password_hash(new_password)
    async def get_stats(self) -> dict:
        from sqlalchemy import func
        from sqlmodel import select
        from app.models.user import User
        from app.models.payment import Payment
        from app.models.transactions import Transaction
        from app.models.propfirm_registration import PropFirmRegistration, AccountStatus

        async def get_count(model):
            query = select(func.count(model.id))
            result = await self.repo.session.exec(query)
            return result.one()

        total_users = await get_count(User)
        total_payments = await get_count(Payment)
        total_transactions = await get_count(Transaction)
        total_registrations = await get_count(PropFirmRegistration)

        # PropFirm Status Counts
        async def get_propfirm_count(status):
            query = select(func.count(PropFirmRegistration.id)).where(PropFirmRegistration.account_status == status)
            result = await self.repo.session.exec(query)
            return result.one()

        propfirm_pending = await get_propfirm_count(AccountStatus.pending)
        propfirm_in_progress = await get_propfirm_count(AccountStatus.in_progress)
        propfirm_passed = await get_propfirm_count(AccountStatus.passed)
        propfirm_failed = await get_propfirm_count(AccountStatus.failed)

        return {
            "total_users": total_users,
            "total_payments": total_payments,
            "total_transactions": total_transactions,
            "total_registrations": total_registrations,
            "propfirm_stats": {
                "pending": propfirm_pending,
                "in_progress": propfirm_in_progress,
                "passed": propfirm_passed,
                "failed": propfirm_failed
            }
        }
