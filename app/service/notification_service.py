from typing import List
from uuid import UUID
from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.notification import Notification, NotificationType
from app.repository.notification_repo import NotificationRepository
from app.schema.notification import NotificationCreate, NotificationUpdate

class NotificationService:
    def __init__(self, session: AsyncSession):
        self.repo = NotificationRepository(Notification, session)

    async def create_notification(self, notification_in: NotificationCreate) -> Notification:
        return await self.repo.create(notification_in)

    async def get_user_notifications(self, user_id: UUID) -> List[Notification]:
        return await self.repo.get_by_user(user_id)

    async def get_admin_notifications(self, admin_id: UUID) -> List[Notification]:
        return await self.repo.get_by_admin(admin_id)

    async def create_status_change_notification(self, user_id: UUID, status: str, propfirm_name: str) -> Notification:
        title = f"PropFirm Account {status.title()}"
        message = f"Your account for {propfirm_name} has been marked as {status}."
        type_map = {
            "passed": NotificationType.PASSED_ACCOUNT,
            "failed": NotificationType.FAILED_ACCOUNT,
            "pending": NotificationType.GENERAL,
            "in_progress": NotificationType.GENERAL
        }
        notification_type = type_map.get(status, NotificationType.GENERAL)

        notification_in = NotificationCreate(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        return await self.create_notification(notification_in)

    async def _get_active_admin_emails(self) -> List[str]:
        from sqlmodel import select
        from app.models.admin import Admin

        # Assuming Status=True means active based on the boolean field in Admin model
        query = select(Admin.email).where(Admin.Status == True)
        result = await self.repo.session.exec(query)
        return result.all()

    async def send_email_to_admins(self, subject: str, template_name: str, context: dict, background_tasks: BackgroundTasks) -> None:
        from app.service.mail import send_email

        admin_emails = await self._get_active_admin_emails()
        for email in admin_emails:
            background_tasks.add_task(
                send_email,
                email_to=email,
                subject=subject,
                template_name=template_name,
                context=context
            )

    # Payment Notifications
    async def create_payment_pending_notification(self, user_id: UUID, order_id: str, amount: float) -> Notification:
        """Create notification for pending payment"""
        notification_in = NotificationCreate(
            user_id=user_id,
            title="Payment Pending",
            message=f"Your payment of ${amount:.2f} for order {order_id} is being processed.",
            type=NotificationType.PAYMENT_PENDING
        )
        return await self.create_notification(notification_in)

    async def create_payment_success_notification(self, user_id: UUID, order_id: str, propfirm_name: str) -> Notification:
        """Create notification for successful payment"""
        notification_in = NotificationCreate(
            user_id=user_id,
            title="Payment Successful",
            message=f"Your payment for {propfirm_name} registration has been completed successfully!",
            type=NotificationType.PAYMENT_SUCCESS
        )
        return await self.create_notification(notification_in)

    async def create_payment_failed_notification(self, user_id: UUID, order_id: str) -> Notification:
        """Create notification for failed payment"""
        notification_in = NotificationCreate(
            user_id=user_id,
            title="Payment Failed",
            message=f"Your payment for order {order_id} could not be processed. Please try again.",
            type=NotificationType.PAYMENT_FAILED
        )
        return await self.create_notification(notification_in)

    async def create_payment_partial_notification(self, user_id: UUID, order_id: str) -> Notification:
        """Create notification for partially paid payment"""
        notification_in = NotificationCreate(
            user_id=user_id,
            title="Partial Payment Received",
            message=f"A partial payment has been received for order {order_id}. The remaining amount is still pending.",
            type=NotificationType.PAYMENT_PARTIAL
        )
        return await self.create_notification(notification_in)

    # Authentication Notifications
    async def create_email_verified_notification(self, user_id: UUID) -> Notification:
        """Create notification for email verification"""
        notification_in = NotificationCreate(
            user_id=user_id,
            title="Email Verified",
            message="Your email has been successfully verified. Welcome aboard!",
            type=NotificationType.EMAIL_VERIFIED
        )
        return await self.create_notification(notification_in)

    async def create_password_changed_notification(self, user_id: UUID) -> Notification:
        """Create notification for password change"""
        notification_in = NotificationCreate(
            user_id=user_id,
            title="Password Changed",
            message="Your password has been successfully updated.",
            type=NotificationType.PASSWORD_CHANGED
        )
        return await self.create_notification(notification_in)

    # Registration Notifications
    async def create_registration_created_notification(self, user_id: UUID, propfirm_name: str, order_id: str) -> Notification:
        """Create notification for new registration"""
        notification_in = NotificationCreate(
            user_id=user_id,
            title="Registration Created",
            message=f"Your {propfirm_name} registration has been created. Order ID: {order_id}. Please complete payment to proceed.",
            type=NotificationType.REGISTRATION_CREATED
        )
        return await self.create_notification(notification_in)

    # Read Status Management
    async def mark_as_read(self, notification_id: UUID) -> Notification | None:
        """Mark a notification as read"""
        notification = await self.repo.get(notification_id)
        if not notification:
            return None

        update_data = NotificationUpdate(is_read=True)
        return await self.repo.update(db_obj=notification, obj_in=update_data.dict(exclude_unset=True))

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all user notifications as read"""
        from sqlmodel import select, update

        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
            .values(is_read=True)
        )
        result = await self.repo.session.execute(stmt)
        await self.repo.session.commit()
        return result.rowcount

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user"""
        from sqlmodel import select, func

        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        result = await self.repo.session.execute(stmt)
        return result.scalar() or 0
