import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/investment_db")

#Silnik - to on faktycznie wysyła dane do Postgresa.
engine = create_async_engine(DATABASE_URL, echo=True)

#Fabryka sesji - każde wejście użytkownika na strone to nowa sesja.
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

#Funckja pomocnicza - daje dostęp do bazy w funkcjach.

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


