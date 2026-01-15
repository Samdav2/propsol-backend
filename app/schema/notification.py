from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.notification import NotificationType

class NotificationBase(BaseModel):
    title: str
    message: str
    type: NotificationType
    user_id: UUID | None = None
    admin_id: UUID | None = None

class NotificationCreate(NotificationBase):
    pass

class NotificationRead(NotificationBase):
    id: UUID
    is_read: bool
    created_at: datetime
    updated_at: datetime

class NotificationUpdate(BaseModel):
    title: str | None = None
    message: str | None = None
    type: NotificationType | None = None
    user_id: UUID | None = None
    admin_id: UUID | None = None
    is_read: bool | None = None
