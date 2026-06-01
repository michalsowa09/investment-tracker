from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .database import engine, get_db
from .models import Base, Asset, Transaction
from sqlalchemy.future import select
from sqlalchemy import or_
import httpx
from .schemas import AssetCreate, AssetResponse

app = FastAPI(title = "Monitor inwestycji") #Tworze swoją aplikację i nadaje jej tytuł.

async def download_rate(currency: str):
    #Adres api NBP (format JSON) - teraz waluta jest zmienna:
    url = f"https://api.nbp.pl/api/exchangerates/rates/a/{currency}/?format=json"

    #Tworzenie "klienta" - który zadzwoni do banku:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)

            #To polecenie samo rzuci błędem, jeśli kod to np. 404 lub 500
            response.raise_for_status()

            data = response.json()
            rate = data["rates"][0]["mid"]
            return rate

        except httpx.HTTPStatusError as e:
            print(f"BŁĄD API: NBP zwrócił kod {e.response.status_code} dla waluty {currency}")
            return None
        except httpx.RequestError as e:
            print(f"BŁĄD POŁĄCZENIA: Nie można połączyć się z serwerem NBP: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"BŁAD DANYCH: Nieoczekiwany format JSON z NBP: {e}")
        except Exception as e:
            print(f"NIEOCZEKIWANY BŁĄD: {e}")
            return None

@app.on_event("startup")#Za każdym razem przy starcie kontenera
async def startup():
    async with engine.begin() as conn:
        #To stworzy bazę danych w Postgresie nawet jak jej nie ma:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/") #"Jeśli ktoś wejdzie na adres główny mojego serwera..."
async def root():# To wtedy uruchamia mi tę funkcję.
    return {"message": "System działa"}

#ENDPOINT DO ZAPISYWANIA DANYCH
@app.post("/aktywa", response_model=AssetResponse)
async def create_asset(asset_data: AssetCreate, db: AsyncSession = Depends(get_db)):
    #Tworznie obiektu klasy asset - dane biorę z obiektu asset_data:
    new_asset = Asset(
        name = asset_data.name,
        ticker = asset_data.ticker,
        amount = asset_data.amount,
        purchase_price = asset_data.purchase_price
    )
    #Dodaję to do sesji - planuję to zapisać.
    db.add(new_asset)
    await db.flush() #pobiera ID zanim zrobi commit
    #Tworzenie śladu w historii:
    history = Transaction(
        asset_id = new_asset.id,
        amount = asset_data.amount,
        price_at_date = asset_data.purchase_price,
    )
    db.add(history) #Dodaję to do sesji
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

#ENDPOINT PRZELICZAJĄCY AKTYWA (UNIWERSLANY) PO AKTUALNYM KURSIE:
@app.get("/wycena/{kod_waluty}")
async def wallet_pricing(currency: str, db: AsyncSession = Depends(get_db)):
    #Pobieranie kursu wybranej waluty (np. eur, isd, gpb):
    rate = await download_rate(currency.lower())
    if rate is None:
        raise HTTPException(status_code = 404, detail = f"NBP nie obsługuje waluty o kodzie: {currency}")

    #Pobranie kursu aktywa i liczenie sumy w PLN

    query = select(Asset)
    result = await db.execute(query)
    assets = result.scalars().all()#lista obiektów

    sum_pln = sum(a.amount * a.purchase_price for a in assets)

    #Przeliczenie na wybraną walutę:
    foreign_sum = sum_pln / rate

    return {
        "Waluta": currency.upper(),
        "Kurs_NBP": rate,
        "Suma_w_pln": round(sum_pln, 2),
        "Wycena_w_obcej_walucie (pln)": round(foreign_sum, 2),
        "komunikat":f"Wycena na podstawie kursu średniego NBP dla: {currency.upper()}"
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
@app.get("/historia")
async def get_all_transactions(db: AsyncSession = Depends(get_db)):
    query = select(Transaction)
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/portfel/analiza")
async def get_portfolio_analysis(db: AsyncSession = Depends(get_db)):
    # 1. Pobieram aktywa z bazy:
    query = select(Asset)
    result = await db.execute(query)
    assets = result.scalars().all()

    analysis = []
    total_invested = 0
    total_current_value = 0

    for a in assets:
        invested = a.amount * a.purchase_price

        # Pobieram kurs dla konkretnego tickera:
        current_unit_price = await download_rate(a.ticker.lower())

        # Jeśli NBP nie ma waluty, używam ceny zakupu (żeby nie było np. -99%):
        if current_unit_price is None:
            current_unit_price = a.purchase_price

        current_value = a.amount * current_unit_price
        profit_loss = current_value - invested

        total_invested += invested
        total_current_value += current_value

        analysis.append({
            "nazwa": a.name,
            "ilosc": a.amount,
            "koszt_zakupu_total": round(invested, 2),
            "wartosc_biezaca_total": round(current_value, 2),
            "zysk_strata": round(profit_loss, 2),
            "procent": round((profit_loss / invested * 100), 2) if invested > 0 else 0
        })

    return {
        "podsumowanie_portfela": {
            "calkowity_koszt": round(total_invested, 2),
            "calkowita_wartosc": round(total_current_value, 2),
            "laczny_zysk_strata": round(total_current_value - total_invested, 2)
        },
        "szczegoly": analysis
    }



