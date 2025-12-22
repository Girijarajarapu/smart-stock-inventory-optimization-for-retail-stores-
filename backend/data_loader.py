# data_loader.py
from datetime import datetime

import pandas as pd
from datasets import load_dataset
from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base
from models import SalesRecord, Inventory


def init_db():
    print("Creating tables (if not exist)...")
    Base.metadata.create_all(bind=engine)


def load_hf_dataset_to_db(limit: int | None = None):
    """
    Loads Rodrigo2204/store-sales-forecast dataset into:
      - sales_records table
      - inventory table (generated from dataset)
    Automatically builds "current_stock" based on average sales.
    """

    print("Loading dataset from Hugging Face...")
    ds = load_dataset("Rodrigo2204/store-sales-forecast", split="train")

    # For faster initial testing
    if limit is not None:
        ds = ds.select(range(limit))

    df = ds.to_pandas()

    # -------------- INSERT INTO sales_records ------------------
    print("Inserting into sales_records...")

    db: Session = SessionLocal()
    try:
        db.query(SalesRecord).delete()

        rows = []
        for _, row in df.iterrows():
            date_val = row["date"]
            if isinstance(date_val, str):
                date_val = datetime.strptime(date_val, "%Y-%m-%d").date()

            rows.append(
                SalesRecord(
                    date=date_val,
                    store_nbr=int(row["store_nbr"]),
                    family=str(row["family"]),
                    sales=float(row["sales"]),
                    onpromotion=int(row.get("onpromotion", 0)),
                )
            )

        db.bulk_save_objects(rows)
        db.commit()
        print(f"Inserted {len(rows)} rows into sales_records.")
    finally:
        db.close()

    # -------------- BUILD INVENTORY FROM DATASET ------------------
    print("Generating inventory from dataset (avg sales per item)...")

    inv_df = (
        df.groupby(["store_nbr", "family"], as_index=False)["sales"]
        .mean()
        .rename(columns={"sales": "avg_sales"})
    )

    # STOCK = 1.2 × avg_sales (assumption)
    inv_df["current_stock"] = inv_df["avg_sales"] * 1.2

    inv_rows = []
    for _, r in inv_df.iterrows():
        inv_rows.append(
            Inventory(
                store_nbr=int(r["store_nbr"]),
                family=str(r["family"]),
                current_stock=float(r["current_stock"]),
            )
        )

    db: Session = SessionLocal()
    try:
        db.query(Inventory).delete()
        db.bulk_save_objects(inv_rows)
        db.commit()
        print(f"Inserted {len(inv_rows)} rows into inventory.")
    finally:
        db.close()

    print("DONE: Sales + Inventory data loaded successfully.")


if __name__ == "__main__":
    init_db()
    # limit=50000 for faster dev; remove limit for full dataset
    load_hf_dataset_to_db(limit=50000)
