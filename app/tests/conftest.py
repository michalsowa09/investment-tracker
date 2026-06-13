import pytest
from app.database import engine
from app.models import Base


# Ten dekorator powie pytestowi, żeby przygotował bazę przed wszystkimi testami
@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    # 1. Tworzymy tabele w czystej bazie GitHuba
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Tu uruchomiają się testy z test_main.py

    # 2. Po testach czysczona jest baza
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)