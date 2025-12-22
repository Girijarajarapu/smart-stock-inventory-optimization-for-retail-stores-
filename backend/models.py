# models.py
from sqlalchemy import Column, Integer, Float, String, Date
from database import Base


class SalesRecord(Base):
    """
    Table for HF dataset:
    Rodrigo2204/store-sales-forecast (simplified)
    """
    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, index=True)
    store_nbr = Column(Integer, index=True)
    family = Column(String(100), index=True)
    sales = Column(Float)
    onpromotion = Column(Integer)  # 0/1 or count of items on promotion


class Inventory(Base):
    """
    Inventory table auto-filled from the dataset.
    For each (store_nbr, family), current_stock is derived from avg sales.
    """
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    store_nbr = Column(Integer, index=True)
    family = Column(String(100), index=True)
    current_stock = Column(Float)
    
from sqlalchemy import DateTime
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(120), unique=True, index=True)
    password_hash = Column(String(255))

    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
