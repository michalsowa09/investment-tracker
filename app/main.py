from fastapi import FastAPI

app = FastAPI(title = "Monitor inwestycji") #Tworze swoją aplikację i nadaje jej tytuł.

@app.get("/") #"Jeśli ktoś wejdzie na adres główny mojego serwera..."
async def root():# To wtedy uruchamia mi tę funkcję.
    return {"message": "System działa"}