import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ----- Create Sample Data -----
start = datetime.today().date() - timedelta(days=6)
rows = []
for store in [1,2]:
    for product in ["Apple","Banana"]:
        stock = 50  # initial stock
        for day in range(7):
            date = start + timedelta(days=day)
            sales = [3,6,2,8,1,5,4][day]  # sample sales
            stock = max(stock - sales, 0)
            rows.append({
                "date": date,
                "store_nbr": store,
                "product": product,
                "sales": sales,
                "stock": stock,
                "item_id": f"{store}_{product}"
            })

df = pd.DataFrame(rows)

# ----- Classify Stock -----
def classify(qty):
    if qty <= 5:
        return "Out of Stock"
    elif qty >= 20:
        return "Overstock"
    else:
        return "Normal Stock"

df['status'] = df['stock'].apply(classify)

# ----- Save CSV -----
df.to_csv("stock_analysis.csv", index=False)
print("Saved stock_analysis.csv")
print(df.head())

# ----- Plot -----
plt.figure(figsize=(10,5))
for item, group in df.groupby('item_id'):
    plt.plot(group['date'], group['stock'], marker='o', label=item)
plt.xlabel("Date")
plt.ylabel("Stock Level")
plt.title("Stock Levels Over Time")
plt.legend()
plt.tight_layout()
plt.savefig("stock_levels.png")
plt.show()
print("Saved stock_levels.png")