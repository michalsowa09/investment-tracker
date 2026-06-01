from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

#Co użytkownik musi wysłać, żeby dodać aktywo:

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=2, example = "Bitcoin")
    ticker: str = Field(..., min_length=2, max_length = 6, example = "BTC")
    amount: float = Field(..., gt=0)#gt=0 - oznaczan : Greater Than 0 (musi być dodatnie)
    purchase_price: float = Field(..., gt=0)

#Jak system ma odpowiadać (co wysyłamy do użytkownika)
class AssetResponse(BaseModel):
    id: int
    name: str
    ticker: str
    amount: float
    purchase_price: float

    class Config:
        from_attributes = True #To pozwala Pydanticowi czytać dane z bazy SQLAlchemy