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
    #Tworznie obiektu klasy asset
    new_asset = Asset(name = name, ticker = ticker, amount = amount, purchase_price = price)
    #Dodaję to do sesji - planuję to zapisać.
    db.add(new_asset)
    #Wysyłam dane do postgresa.
    await db.commit()
    #Robię odświeżenie - czyli mówię pobierz z bazy to co zapisałem i uzupełnij mój obiekt o ewentualne braki.
    await db.refresh(new_asset)
    #Zrwacam obiekt klasy Asset
    return new_asset

#ENDPOINT DO POBIERANIA WSZYSTKICH DANYCH:

@app.get("/assets")
async def get_all_assets(db: AsyncSession = Depends(get_db)):
    #tworzenie zapytania - pobranie wszystkiego z tabeli asset:
    query = select(Asset)

    #Wykonuje zapytanie w bazie danych:
    result = await db.execute(query)
    #Wyciąganie samych obiektów jako listę
    assets_list = result.scalars().all()
    return assets_list

#ENDPOINT LICZĄCY ŁĄCZNĄ WARTOŚĆ ZAKUPÓW:
@app.get("/total-value")
async def get_total_value(db: AsyncSession = Depends(get_db)):
    query = select(Asset)
    #Wykonuje zapytanie do bazy danych:
    result = await db.execute(query)
    #Zwrócenie wyniku w postaci listy obiektów:
    assets_list = result.scalars().all()

    total_value = 0
    for i in range(len(assets_list)):
        total_value += assets_list[i].amount * assets_list[i].purchase_price

    return {
        "Suma_wydatków": total_value,
        "Liczba_aktywów": len(assets_list)
    }


