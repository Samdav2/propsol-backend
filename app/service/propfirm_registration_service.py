from uuid import UUID
from typing import List
from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.propfirm_registration import PropFirmRegistration
from app.models.user import User
from app.schema.propfirm_registration import PropFirmRegistrationCreate, PropFirmRegistrationUpdate
from app.repository.propfirm_registration_repo import PropFirmRegistrationRepository
from app.utils.order_id import generate_order_id

class PropFirmRegistrationService:
    def __init__(self, session: AsyncSession):
        self.repo = PropFirmRegistrationRepository(PropFirmRegistration, session)

    async def create_registration(self, registration_in: PropFirmRegistrationCreate, user_id: UUID) -> PropFirmRegistration:
        registration_data = registration_in.dict()
        registration_data["user_id"] = user_id
        registration_data["order_id"] = generate_order_id()
        return await self.repo.create(registration_data)

    async def get_registrations_by_user(self, user_id: UUID, status: str | None = None) -> List[PropFirmRegistration]:
        return await self.repo.get_by_user(user_id, status)

    async def get_registration(self, registration_id: UUID) -> PropFirmRegistration | None:
        return await self.repo.get(registration_id)

    async def update_registration(self, registration_id: UUID, update_data: PropFirmRegistrationUpdate, background_tasks: BackgroundTasks) -> PropFirmRegistration | None:
        registration = await self.repo.get(registration_id)
        if not registration:
            return None

        # Check if status is changing
        old_status = registration.account_status
        updated_registration = await self.repo.update(db_obj=registration, obj_in=update_data.dict(exclude_unset=True))

        if update_data.account_status and update_data.account_status != old_status:
            from app.service.notification_service import NotificationService
            notification_service = NotificationService(self.repo.session)
            await notification_service.create_status_change_notification(
                user_id=updated_registration.user_id,
                status=updated_registration.account_status,
                propfirm_name=updated_registration.propfirm_name
            )
            await self.repo.session.refresh(updated_registration)

            # Notify Admin
            from app.service.mail import send_email
            from app.config import settings
            from app.models.propfirm_registration import AccountStatus

            user = None
            if settings.ADMIN_EMAIL:
                template = None
                subject = None
                if updated_registration.account_status == AccountStatus.passed:
                    template = "admin_account_passed.html"
                    subject = "Prop Firm Account Passed"
                elif updated_registration.account_status == AccountStatus.failed:
                    template = "admin_account_failed.html"
                    subject = "Prop Firm Account Failed"

                if template:
                    # Fetch user email
                    user = await self.repo.session.get(User, updated_registration.user_id)
                    user_email = user.email if user else "Unknown"

                    background_tasks.add_task(
                        send_email,
                        email_to=settings.ADMIN_EMAIL,
                        subject=subject,
                        template_name=template,
                        context={
                            "user_email": user_email,
                            "propfirm_name": updated_registration.propfirm_name,
                            "login_id": updated_registration.login_id
                        }
                    )

            # Ensure user is fetched for user notification
            if not user:
                user = await self.repo.session.get(User, updated_registration.user_id)

            # Notify User
            if user:
                user_template = None
                user_subject = None
                if updated_registration.account_status == AccountStatus.passed:
                    user_template = "user_account_passed.html"
                    user_subject = "Congratulations! You Passed!"
                elif updated_registration.account_status == AccountStatus.failed:
                    user_template = "user_account_failed.html"
                    user_subject = "Prop Firm Challenge Update"

                if user_template:
                    background_tasks.add_task(
                        send_email,
                        email_to=user.email,
                        subject=user_subject,
                        template_name=user_template,
                        context={
                            "name": user.name,
                            "propfirm_name": updated_registration.propfirm_name,
                            "login_id": updated_registration.login_id
                        }
                    )

        return updated_registration
