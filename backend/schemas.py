# schemas.py
from datetime import date
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    store_nbr: int
    family: str
    date: date
    onpromotion: int = 0


class PredictionResponse(BaseModel):
    store_nbr: int
    family: str
    date: date
    onpromotion: int
    predicted_sales: float


class MetricsResponse(BaseModel):
    mae: float
    rmse: float
    r2: float


class StockStatusRequest(BaseModel):
    store_nbr: int
    family: str
    date: date
    onpromotion: int = 0
    current_stock: float


class StockStatusResponse(BaseModel):
    store_nbr: int
    family: str
    date: date
    onpromotion: int
    current_stock: float
    predicted_sales: float
    status: str  # "overstock", "understock", "ok"
    shortage_or_excess: float  # +ve = extra, -ve = shortage
    message: str


class AutoStockItem(BaseModel):
    store_nbr: int
    family: str
    current_stock: float
    predicted_sales: float
    status: str
    shortage_or_excess: float
    message: str


class AutoStockResponse(BaseModel):
    date: date
    items: list[AutoStockItem]


# ---------- NEW: Inventory CRUD schemas ----------
class ItemRequest(BaseModel):
    store_nbr: int = Field(..., example=1)
    family: str = Field(..., example="GROCERY I")
    current_stock: float = Field(..., example=120.5)


class ItemResponse(BaseModel):
    id: int
    store_nbr: int
    family: str
    current_stock: float


class ItemListResponse(BaseModel):
    items: list[ItemResponse]

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    id: int
    name: str
    email: str
    token: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
