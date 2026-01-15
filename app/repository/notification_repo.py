from typing import List
from uuid import UUID
from sqlmodel import select

from app.models.notification import Notification
from app.schema.notification import NotificationCreate, NotificationUpdate
from app.repository.base_repo import BaseRepository

class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationUpdate]):
    async def get_by_user(self, user_id: UUID) -> List[Notification]:
        query = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.desc())
        result = await self.session.exec(query)
        return result.all()

    async def get_by_admin(self, admin_id: UUID) -> List[Notification]:
        query = select(self.model).where(self.model.admin_id == admin_id).order_by(self.model.created_at.desc())
        result = await self.session.exec(query)
        return result.all()
