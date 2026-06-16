import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text  # Add this import

async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:1234@localhost:5432/jobautomation')
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT 1'))  # Wrap in text()
        print('Connection successful:', result.scalar())
    await engine.dispose()

asyncio.run(test())