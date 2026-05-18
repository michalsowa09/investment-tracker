from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .database import engine, get_db
from .models import Base, Asset
from sqlalchemy.future import select
from sqlalchemy import or_
import httpx

app = FastAPI(title = "Monitor inwestycji") #Tworze swoją aplikację i nadaje jej tytuł.

async def download_usd_rate():
    #Adres api NBP dla kursu dolara (format JSON):
    url = "https://api.nbp.pl/api/exchangerates/rates/a/usd/?format=json"

    #Tworzenie "klienta" - który zadzwoni do banku:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)

            #Sprawdzenie, czy bank poprawnie odpowiedział
            if response.status_code == 200:
                data = response.json()

                #Wyciągam samą liczbę(kurs) z ich JSONA:
                rate = data["rates"][0]["mid"]
                return rate
        except(httpx.HTTPStatusError, httpx.RequestError, keyError):
            #Jeśli bank nie odpowie - zwracam domyślną wartość - ja ustawiam 4
            print("BŁĄD: Nie udałom się pobrać kursu NBP, używam kursu zastępczego: 4.0")
            return 4.0

@app.on_event("startup")#Za każdym razem przy starcie kontenera
async def startup():
    async with engine.begin() as conn:
        #To stworzy bazę danych w Postgresie nawet jak jej nie ma:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/") #"Jeśli ktoś wejdzie na adres główny mojego serwera..."
async def root():# To wtedy uruchamia mi tę funkcję.
    return {"message": "System działa"}

#ENDPOINT DO ZAPISYWANIA DANYCH
@app.post("/aktywa")
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
@app.get("/aktywa")
async def get_all_assets(db: AsyncSession = Depends(get_db)):
    #tworzenie zapytania - pobranie wszystkiego z tabeli asset:
    query = select(Asset)

    #Wykonuje zapytanie w bazie danych:
    result = await db.execute(query)
    #Wyciąganie samych obiektów jako listę
    assets_list = result.scalars().all()
    return assets_list

#ENDPOINT LICZĄCY ŁĄCZNĄ WARTOŚĆ ZAKUPÓW:
@app.get("/podsumowanie")
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

#ENDPOINT PRZELICZAJĄCY AKTYWA NA USD PO AKTUALNYM KURSIE:
@app.get("/wycena-usd")
async def get_usd_valuation(db: AsyncSession = Depends(get_db)):

    #1. Pobieram kurs z NBP
    usd_rate = await download_usd_rate()

    #2. Pobieram aktywa z bazy danych:
    query = select(Asset)
    result = await db.execute(query)
    assets_list = result.scalars().all()

    #Liczę wartość w złotówkach:
    pln_sum = sum(assets_list[i].amount * assets_list[i].purchase_price for i in range(len(assets_list)))

    #Przeliczam na dolary po aktualnym kursie:
    usd_sum = pln_sum/usd_rate

    return {
        "Aktualny_kurs_nbp": usd_rate,
        "Suma_w_pln": pln_sum,
        "Suma_w_usd": usd_sum,
        "Wiadomosc": "Dane pobrano z NBP"
    }

#ENDPOINT USUWAJĄCY AKTYWO O KONKRETNYM ID:
@app.delete("/aktywa/{id_asset}")
async def remove_asset(id_asset: int, db: AsyncSession = Depends(get_db)):
    #1. Szukam aktywa o konkretnym ID:
    query = select(Asset).where(Asset.id == id_asset)
    result = await db.execute(query)
    asset = result.scalar_one_or_none()#Zwóci albo jeden konkretnyn rekord, albo none - czyli nic

    #3. Jeżeli nie ma takiego aktywa - rzucam błędem 404:
    if asset is None:
        raise HTTPException(status_code=404, detail = "Nie ma takiego aktywa w bazie")

    #3. Jeżeli jest, to usuwam:
    await db.delete(asset)
    await db.commit()#wysyłam do bazy (wykonanie transakcji).

    return {"message": f"Aktywo o ID {id_asset} zostało usunięte"}

#ENDPOINT AKTUALIZUJĄCY AKTYWO O KONKRETNYM ID:
@app.put("/aktywa/{id_asset}/dokup")
async def buy_more(id_asset: int, added_amount: float, added_price: float, db: AsyncSession = Depends(get_db)):
    #1. Pobieram z bazy to, co aktualnie się w niej znajduje:
    query = select(Asset).where(Asset.id == id_asset)
    result = await db.execute(query)
    asset = result.scalar_one_or_none()

    if asset is None:
        raise HTTPException(status_code = 404, detail = "Nie ma takiego aktywa - błędnę ID")

    #2.Liczenie:
    old_value = asset.amount * asset.purchase_price #Ile zostało wydane wcześniej
    new_value = added_amount * added_price #Ile zostaje wydane teraz

    summary = asset.amount + added_amount #Suma sztuk
    new_avarage_price = (old_value + new_value) / summary

    #3. Nadpisanie staryh pul nowymi wartościami:

    asset.amount = summary
    asset.purchase_price = new_avarage_price

    await db.commit()
    await db.refresh(asset)

    return {
        "Komunikat":"Pomyślnie dokupiono i przeliczono cenę",
        "Nowy_stan": asset
    }

#ENDPOINT - WYSZUKIWARKA (FILTROWANIE DANYCH):
@app.get("/aktywa/szukaj")
async def search_asset(phrase: str, db: AsyncSession = Depends(get_db)):
    #1. Tworze zapytanie z filtrem
    #ilike - szukanie tekstu bez względu na wilekość liter
    #%{phrase}% - coś może być przed frazą i po niej

    query = select(Asset).where(or_(Asset.name.ilike(f"%{phrase}%"), Asset.ticker.ilike(f"%{phrase}%")))

    #Wykonanie zapytania:
    result = await db.execute(query)
    found = result.scalars().all()
    return {
        "Wynik": found,
        "Liczba_znalezionych": len(found)
    }