# SmartStock - Intelligent Retail Inventory Optimization

SmartStock is a comprehensive **E-Commerce & ERP solution** designed to optimize retail store inventory using **Machine Learning**. It helps store managers prevent stockouts and overstocking by forecasting demand, analyzing sales patterns, and automating alert systems.

Built for the **E-Commerce & ERP (PEC-AIML 702A)** curriculum.

---

## 🚀 Key Features

### 🧠 Machine Learning & Forecasting
- **Demand Prediction:** Uses `HistGradientBoostingRegressor` to predict future sales based on historical data.
- **Custom Range Forecast:** Visual graphs showing predicted sales trends for the next 7, 30, or 365 days.
- **Stock Status Classification:** Automatically classifies items as **Overstock**, **Understock**, or **Stockout**.

### 📊 Advanced Analytics
- **ABC Analysis:** Categorizes inventory into High (A), Medium (B), and Low (C) value items based on the Pareto Principle (80/20 rule).
- **Anomaly Detection:** Detects sales spikes and theft using Z-Score statistical analysis.
- **Market Basket Analysis:** Identifies product correlation (items frequently bought together) to aid cross-selling.
- **Inter-Store Transfer:** Intelligent optimizer that suggests moving stock from "Overstock" stores to "Understock" stores to balance inventory.

### 🔔 Automation & Alerts
- **Smart Notification System:** Triggers Email and SMS alerts to the Admin when critical stock levels are breached.
- **Demo Simulation Mode:** Includes a safe simulation mode for presentations to demonstrate alert logic without triggering spam blockers.

### 🛠️ ERP Utilities
- **Inventory CRUD:** Full Create, Read, Update, Delete functionality for inventory items.
- **AI Chatbot:** Built-in Natural Language chatbot to query stock levels and predictions (e.g., *"Stock of GROCERY I in store 1"*).
- **User Authentication:** Secure Login and Registration system using JWT (JSON Web Tokens).

---

## 🏗️ Tech Stack

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI (High-performance API)
- **Database:** MySQL (Relational Data Storage)
- **ORM:** SQLAlchemy
- **ML Libraries:** Scikit-Learn, Pandas, NumPy

### Frontend
- **Interface:** HTML5, CSS3 (Custom Dark/Light Theme)
- **Logic:** Vanilla JavaScript (ES6+)
- **Charts:** Chart.js

### Integrations
- **Email:** SMTP (Gmail)
- **SMS:** Twilio API

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/smartstock.git](https://github.com/yourusername/smartstock.git)
cd smartstock
