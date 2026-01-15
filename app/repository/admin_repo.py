from typing import Optional
from sqlmodel import select
from app.models.admin import Admin
from app.schema.admin import AdminCreate, AdminUpdate
from app.repository.base_repo import BaseRepository

class AdminRepository(BaseRepository[Admin, AdminCreate, AdminUpdate]):
    async def get_by_email(self, email: str) -> Optional[Admin]:
        query = select(self.model).where(self.model.email == email)
        result = await self.session.exec(query)
        return result.first()
