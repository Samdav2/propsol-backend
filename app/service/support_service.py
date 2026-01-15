from fastapi import BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.support import Support
from app.schema.support import SupportCreate
from app.repository.support_repo import SupportRepository

class SupportService:
    def __init__(self, session: AsyncSession):
        self.repo = SupportRepository(Support, session)

    async def create_support_ticket(self, support_in: SupportCreate, background_tasks: BackgroundTasks) -> Support:
        support = await self.repo.create(support_in)

        from app.service.mail import send_email
        background_tasks.add_task(
            send_email,
            email_to=support.email,
            subject="Support Request Received",
            template_name="support_receipt.html",
            context={"name": support.name, "message": support.message}
        )
        return support
