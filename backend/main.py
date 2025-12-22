# main.py
import uuid
from datetime import datetime, timedelta
from schemas import ForgotPasswordRequest, ResetPasswordRequest

from datetime import date as date_type, timedelta

import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, engine, Base
from ml_model import DemandForecaster
from models import Inventory, SalesRecord
from schemas import (
    PredictionRequest,
    PredictionResponse,
    MetricsResponse,
    StockStatusRequest,
    StockStatusResponse,
    AutoStockItem,
    AutoStockResponse,
    ItemRequest,
    ItemResponse,
    ItemListResponse,
)
from data_loader import load_hf_dataset_to_db  # used by /reload-data

app = FastAPI(title="SmartStock Backend")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g. ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
forecaster = DemandForecaster()


@app.on_event("startup")
def startup_event():
    """
    1) Create tables in MySQL if they don't exist.
    2) Train model using data from DB.
    """
    Base.metadata.create_all(bind=engine)

    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        forecaster.train(db)
        print("ML model trained. Metrics:", forecaster.metrics)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.get("/health")
def health():
    return {"status": "ok", "message": "SmartStock backend running"}


@app.get("/metrics", response_model=MetricsResponse)
def get_model_metrics():
    if forecaster.metrics is None:
        raise HTTPException(status_code=500, detail="Model not trained yet.")
    return forecaster.metrics


@app.post("/predict", response_model=PredictionResponse)
def predict_sales(req: PredictionRequest):
    try:
        y_hat = forecaster.predict(
            store_nbr=req.store_nbr,
            family=req.family,
            date_str=req.date,
            onpromotion=req.onpromotion,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return PredictionResponse(
        store_nbr=req.store_nbr,
        family=req.family,
        date=req.date,
        onpromotion=req.onpromotion,
        predicted_sales=y_hat,
    )


@app.post("/stock-status", response_model=StockStatusResponse)
def stock_status(req: StockStatusRequest):
    """
    Manual check for one item – optional.
    """
    if forecaster.pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Model not available. Train model or check logs.",
        )

    try:
        predicted = forecaster.predict(
            store_nbr=req.store_nbr,
            family=req.family,
            date_str=req.date,
            onpromotion=req.onpromotion,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    demand = float(predicted)
    stock = float(req.current_stock)

    overstock_threshold = 1.2
    understock_threshold = 0.8

    status = "ok"
    message = "Stock level is balanced for predicted demand."
    shortage_or_excess = stock - demand  # +ve: extra, -ve: shortage

    if stock > overstock_threshold * demand:
        status = "overstock"
        message = (
            f"Overstock: Current stock ({stock:.1f}) is much higher than predicted demand "
            f"({demand:.1f}). Consider slowing orders or promotion."
        )
    elif stock < understock_threshold * demand:
        status = "understock"
        message = (
            f"Understock: Current stock ({stock:.1f}) is lower than predicted demand "
            f"({demand:.1f}). Consider reordering."
        )

    return StockStatusResponse(
        store_nbr=req.store_nbr,
        family=req.family,
        date=req.date,
        onpromotion=req.onpromotion,
        current_stock=stock,
        predicted_sales=demand,
        status=status,
        shortage_or_excess=shortage_or_excess,
        message=message,
    )


@app.get("/auto-stock-status", response_model=AutoStockResponse)
def auto_stock_status(
    target_date: date_type | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    (existing auto-stock-status route preserved unchanged)
    """
    if forecaster.pipeline is None:
        raise HTTPException(status_code=503, detail="Model not trained.")

    if target_date is None:
        target_date = date_type.today()

    # ---------- 1) Try using Inventory table ----------
    inv_rows = db.query(Inventory).all()
    inventory_records: list[dict] = []
    source = "inventory"

    if inv_rows:
        # Real inventory from DB
        for r in inv_rows:
            inventory_records.append(
                {
                    "store_nbr": r.store_nbr,
                    "family": r.family,
                    "current_stock": float(r.current_stock),
                }
            )
    else:
        # ---------- 2) Fallback: build virtual inventory from SalesRecord ----------
        print("No inventory data found. Building virtual inventory from sales_records...")
        sales_rows = db.query(SalesRecord).all()
        if not sales_rows:
            raise HTTPException(
                status_code=404,
                detail="No sales data found in sales_records. Run data_loader.py.",
            )

        data = [
            {
                "store_nbr": r.store_nbr,
                "family": r.family,
                "sales": r.sales,
            }
            for r in sales_rows
        ]
        df = pd.DataFrame(data)

        agg = (
            df.groupby(["store_nbr", "family"], as_index=False)["sales"]
            .mean()
            .rename(columns={"sales": "avg_sales"})
        )
        # Assume current_stock ~ 1.2 * avg sales
        agg["current_stock"] = agg["avg_sales"] * 1.2

        source = "sales_records"
        for _, row in agg.iterrows():
            inventory_records.append(
                {
                    "store_nbr": int(row["store_nbr"]),
                    "family": str(row["family"]),
                    "current_stock": float(row["current_stock"]),
                }
            )

    if not inventory_records:
        raise HTTPException(
            status_code=404,
            detail="Could not build inventory data from dataset.",
        )

    # ---------- Predict demand for all inventory items ----------
    feature_rows = []
    for rec in inventory_records:
        feature_rows.append(
            {
                "date": target_date,
                "store_nbr": rec["store_nbr"],
                "family": rec["family"],
                "onpromotion": 0,
            }
        )

    feature_df = pd.DataFrame(feature_rows)
    feature_df = forecaster._add_date_features(feature_df)
    preds = forecaster.pipeline.predict(feature_df)

    overstock_threshold = 1.2
    understock_threshold = 0.8

    items: list[AutoStockItem] = []

    for i, rec in enumerate(inventory_records):
        demand = float(preds[i])
        stock = float(rec["current_stock"])
        shortage_or_excess = stock - demand

        status = "ok"
        message = f"Stock level is balanced for predicted demand. [source={source}]"

        if stock > demand * overstock_threshold:
            status = "overstock"
            message = (
                f"Overstock: Current stock ({stock:.1f}) is much higher than predicted demand "
                f"({demand:.1f}). Consider slowing orders or promotion. [source={source}]"
            )
        elif stock < demand * understock_threshold:
            status = "understock"
            message = (
                f"Understock: Current stock ({stock:.1f}) is lower than predicted demand "
                f"({demand:.1f}). Consider reordering. [source={source}]"
            )

        items.append(
            AutoStockItem(
                store_nbr=rec["store_nbr"],
                family=rec["family"],
                current_stock=stock,
                predicted_sales=demand,
                status=status,
                shortage_or_excess=shortage_or_excess,
                message=message,
            )
        )

    return AutoStockResponse(
        date=target_date,
        items=items,
    )


# ---------- OPTIONAL: reload HF dataset & retrain (frontend is not using it now) ----------
@app.post("/reload-data")
def reload_data(limit: int | None = 50000):
    """
    Reload HF dataset (Rodrigo2204/store-sales-forecast) into MySQL
    and retrain the ML model.
    """
    try:
        Base.metadata.create_all(bind=engine)
        load_hf_dataset_to_db(limit=limit)

        db_gen = get_db()
        db: Session = next(db_gen)
        try:
            forecaster.train(db)
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

        return {
            "status": "ok",
            "message": "Dataset imported from Hugging Face and model retrained.",
            "limit_used": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- NEW: Inventory CRUD endpoints ----------
@app.get("/items", response_model=ItemListResponse)
def list_items(
    search: str | None = Query(default=None, description="search by family substring"),
    store_nbr: int | None = Query(default=None, description="filter by store number"),
    db: Session = Depends(get_db),
):
    """
    List inventory items. Optional search by family (case-insensitive substring) and store filter.
    """
    q = db.query(Inventory)
    if store_nbr is not None:
        q = q.filter(Inventory.store_nbr == store_nbr)
    if search:
        q = q.filter(Inventory.family.ilike(f"%{search}%"))

    rows = q.order_by(Inventory.store_nbr, Inventory.family).all()
    items = [
        ItemResponse(id=r.id, store_nbr=r.store_nbr, family=r.family, current_stock=float(r.current_stock))
        for r in rows
    ]
    return ItemListResponse(items=items)


@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(req: ItemRequest, db: Session = Depends(get_db)):
    """
    Create inventory item. If a (store_nbr, family) pair already exists we return 409.
    """
    # check duplicate by (store_nbr, family)
    exists = (
        db.query(Inventory)
        .filter(Inventory.store_nbr == req.store_nbr)
        .filter(Inventory.family == req.family)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Item already exists. Use update endpoint.")

    item = Inventory(store_nbr=req.store_nbr, family=req.family, current_stock=req.current_stock)
    db.add(item)
    db.commit()
    db.refresh(item)

    return ItemResponse(id=item.id, store_nbr=item.store_nbr, family=item.family, current_stock=float(item.current_stock))


@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int = Path(..., description="Inventory item ID"),
    req: ItemRequest = None,
    db: Session = Depends(get_db),
):
    """
    Update an existing inventory item by id.
    """
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    item.store_nbr = req.store_nbr
    item.family = req.family
    item.current_stock = req.current_stock

    db.add(item)
    db.commit()
    db.refresh(item)

    return ItemResponse(id=item.id, store_nbr=item.store_nbr, family=item.family, current_stock=float(item.current_stock))


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int = Path(..., description="Inventory item ID"), db: Session = Depends(get_db)):
    """
    Delete inventory item by id.
    """
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    db.delete(item)
    db.commit()
    return None


# ---------- NEW: range-forecast, etc. (preserved above) ----------
# (Range forecast route and other existing code remain unchanged)
from fastapi import Query  # agar already imported nahin hai, upar waale imports me add kar lo
# --- add this route somewhere in main.py (near other routes) ---

@app.get("/range-forecast")
def range_forecast(
    store_nbr: int = Query(..., description="Store number"),
    family: str = Query(..., description="Family name (case-sensitive, try variants)"),
    days: int = Query(30, description="Number of days to return (default 30)"),
    db: Session = Depends(get_db),
):
    """
    Return a time series (points) of predicted sales for the given store+family
    for the last `days` days (ending today). Response:
      { "store_nbr": ..., "family": "...", "points": [ {"date":"YYYY-MM-DD", "predicted_sales": float}, ... ] }
    """
    if forecaster.pipeline is None:
        raise HTTPException(status_code=503, detail="Model not trained. Train model or check logs.")

    if days <= 0 or days > 365:
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")

    try:
        # build dates: last `days` days ending today
        end_date = date_type.today()
        start_date = end_date - timedelta(days=days - 1)

        dates = [start_date + timedelta(days=i) for i in range(days)]

        # Build feature dataframe expected by forecaster.predict pipeline
        feature_rows = [
            {"date": d, "store_nbr": int(store_nbr), "family": str(family), "onpromotion": 0}
            for d in dates
        ]
        feature_df = pd.DataFrame(feature_rows)

        # use the forecaster's helper to add date features (year/month/day/dow)
        feature_df = forecaster._add_date_features(feature_df)

        preds = forecaster.pipeline.predict(feature_df)

        points = []
        for i, d in enumerate(dates):
            val = float(preds[i]) if i < len(preds) else 0.0
            points.append({"date": d.isoformat(), "predicted_sales": val})

        return {"store_nbr": store_nbr, "family": family, "points": points}
    except Exception as e:
        # include error so frontend diagnostic shows something useful
        raise HTTPException(status_code=500, detail=f"range-forecast error: {e}")


from auth_utils import hash_password, verify_password, create_jwt
from models import User
from schemas import RegisterRequest, LoginRequest, AuthResponse
from fastapi import Header

@app.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_jwt(user.id, user.email)
    return AuthResponse(id=user.id, name=user.name, email=user.email, token=token)


@app.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    token = create_jwt(user.id, user.email)
    return AuthResponse(id=user.id, name=user.name, email=user.email, token=token)
@app.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered.")

    token = str(uuid.uuid4())
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=10)

    db.commit()

    # Normally yaha email bhejte
    return {
        "message": "Reset token generated",
        "reset_token": token   # ⚠️ demo purpose only
    }
@app.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == req.token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token.")

    if user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired.")

    user.password_hash = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return {"message": "Password updated successfully."}

from alert_service import check_stock_and_alert



from alert_service import check_stock_and_alert
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

@app.post("/check-stock-alerts")
def trigger_stock_alerts(db: Session = Depends(get_db)):
    check_stock_and_alert(db)
    return {"message": "Stock alerts sent successfully"}

from fastapi import Body
from alert_settings import get_settings, update_settings

@app.get("/alert-settings")
def fetch_alert_settings():
    return get_settings()

@app.post("/alert-settings")
def change_alert_settings(
    email: bool = Body(...),
    sms: bool = Body(...)
):
    update_settings(email, sms)
    return {"message": "Alert settings updated"}
