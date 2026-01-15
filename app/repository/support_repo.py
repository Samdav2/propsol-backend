from app.models.support import Support
from app.schema.support import SupportCreate
from app.repository.base_repo import BaseRepository

class SupportRepository(BaseRepository[Support, SupportCreate, SupportCreate]):
    pass
