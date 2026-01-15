from uuid import UUID
from typing import List
from sqlmodel import select
from app.models.propfirm_registration import PropFirmRegistration
from app.schema.propfirm_registration import PropFirmRegistrationCreate, PropFirmRegistrationUpdate
from app.repository.base_repo import BaseRepository

class PropFirmRegistrationRepository(BaseRepository[PropFirmRegistration, PropFirmRegistrationCreate, PropFirmRegistrationUpdate]):
    async def get_by_user(self, user_id: UUID, status: str | None = None) -> List[PropFirmRegistration]:
        query = select(self.model).where(self.model.user_id == user_id)
        if status:
            query = query.where(self.model.account_status == status)
        result = await self.session.exec(query)
        return result.all()

    async def get_by_order_id(self, order_id: str) -> PropFirmRegistration | None:
        """Find propfirm registration by order_id"""
        query = select(self.model).where(self.model.order_id == order_id)
        result = await self.session.exec(query)
        return result.first()
