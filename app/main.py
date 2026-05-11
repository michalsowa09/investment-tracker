from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import engine, get_db
from .models import Base, Asset
from sqlalchemy.future import select

app = FastAPI(title = "Monitor inwestycji") #Tworze swoją aplikację i nadaje jej tytuł.


@app.on_event("startup")#Za każdym razem przy starcie kontenera
async def startup():
    async with engine.begin() as conn:
        #To stworzy bazę danych w Postgresie nawet jak jej nie ma:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/") #"Jeśli ktoś wejdzie na adres główny mojego serwera..."
async def root():# To wtedy uruchamia mi tę funkcję.
    return {"message": "System działa"}

#ENDPOINT DO ZAPISYWANIA DANYCH
@app.post("/assets")
async def create_asset(name: str, ticker: str, amount: float, price: float, db:
AsyncSession = Depends(get_db)):
    new_asset = Asset(name = name, ticker = ticker, amount = amount, purchase_price = price)
    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)
    return new_asset
