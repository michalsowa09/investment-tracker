import pytest
from app.database import engine
from app.models import Base


# Zmieniamy scope na "function" (domyślny) - to naprawi błąd ScopeMismatch
@pytest.fixture(autouse=True)
async def setup_database():
    # 1. Przed KAŻDYM testem tworzymy tabele od zera
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Tu uruchamia się test

    # 2. Po KAŻDYM teście czyścimy bazę, żeby następny miał czyste pole
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)