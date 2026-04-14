from core.database import db_client


async def get_db() -> db_client.get_session:
    async for session in db_client.get_session():
        yield session