from uuid import UUID
from typing import List
from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.payment import Payment
from app.schema.payment import PaymentCreate, PaymentUpdate
from app.repository.payment_repo import PaymentRepository

class PaymentService:
    def __init__(self, session: AsyncSession):
        self.repo = PaymentRepository(Payment, session)

    async def create_payment(self, payment_in: PaymentCreate, user_id: UUID, background_tasks: BackgroundTasks) -> Payment:
        # Manually create dict and add user_id
        payment_data = payment_in.dict()
        payment_data["user_id"] = user_id
        payment = await self.repo.create(payment_data)

        # Notify Admin
        from app.service.mail import send_email
        from app.config import settings
        from app.models.user import User

        if settings.ADMIN_EMAIL:
            # Fetch user email
            user = await self.repo.session.get(User, user_id)
            user_email = user.email if user else "Unknown"

            background_tasks.add_task(
                send_email,
                email_to=settings.ADMIN_EMAIL,
                subject="Payment Received",
                template_name="admin_payment_received.html",
                context={
                    "user_email": user_email,
                    "amount": payment.amount,
                    "reference": payment.reference or "N/A",
                    "created_at": payment.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        return payment

    async def get_payments_by_user(self, user_id: UUID) -> List[Payment]:
        return await self.repo.get_by_user(user_id)

    async def get_payment(self, payment_id: UUID) -> Payment | None:
        return await self.repo.get(payment_id)

    async def delete_payment(self, payment_id: UUID) -> Payment | None:
        return await self.repo.delete(id=payment_id)
