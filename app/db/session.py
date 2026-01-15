from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

connect_args = {}
if settings.db_uri.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.db_uri,
    echo=True,
    future=True,
    # pool_size=20, # SQLite doesn't support pool_size in the same way, and it can cause issues if not handled carefully.
    # max_overflow=10,
    connect_args=connect_args,
)

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
