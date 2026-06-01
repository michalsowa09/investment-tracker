from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)#np. "Bitcoin"
    ticker = Column(String)#np. "Btc"
    amount = Column(Float)#np. "0.5"
    purchase_price = Column(Float)#np. 45000.0
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    #Tutaj tak jakby mówię, że "asset - ma wiele transakcji"
    transactions = relationship("Transaction", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("asset.id")) #Połączenie z asset
    amount = Column(Float)
    price_at_date = Column(Float)
    date = created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("Asset", back_populates="transactions")