# 📈 Stock Portfolio Tracker

A **Django + MySQL** web application that lets you build and track a simulated stock portfolio using fixed sample prices.

> ⚠️ **Sample Prices Only** — Stock prices are manually defined for demonstration purposes. This project does NOT fetch live market data.

---

## 🖥️ Preview

| Feature | Description |
|---------|-------------|
| Dashboard | Total investment, holdings count, total shares |
| Add Stock | Select from 7 stocks, enter quantity, see live preview |
| Portfolio Table | Symbol, price, quantity, investment value, date added |
| Edit / Delete | Update quantity or remove a holding |
| CSV Export | Download portfolio as a spreadsheet |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13 · Django 4.2 |
| Database | MySQL 8 via XAMPP |
| Frontend | Plain HTML · CSS · JavaScript (no frameworks) |
| DB Driver | mysqlclient 2.3.0 |

---

## 📦 Supported Stocks (Sample Prices)

| Symbol | Company | Price (USD) |
|--------|---------|-------------|
| AAPL | Apple Inc. | $180.00 |
| TSLA | Tesla Inc. | $250.00 |
| GOOGL | Alphabet Inc. | $150.00 |
| MSFT | Microsoft Corporation | $420.00 |
| AMZN | Amazon.com Inc. | $190.00 |
| NVDA | NVIDIA Corporation | $120.00 |
| META | Meta Platforms Inc. | $500.00 |

---

## 🚀 Local Setup

### Prerequisites
- Python 3.10+
- XAMPP (Apache + MySQL)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/stock-portfolio-tracker.git
cd stock-portfolio-tracker
```

### 2. Create & Activate Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start XAMPP

- Open **XAMPP Control Panel**
- Start **Apache** and **MySQL**

### 5. Create the Database

- Open `http://localhost/phpmyadmin`
- Create a new database: **`stockportfolio`**
- Collation: `utf8mb4_general_ci`

### 6. Configure Database (if needed)

Open `config/config/settings.py` and verify:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'stockportfolio',
        'USER': 'root',
        'PASSWORD': '',       # change if your MySQL has a password
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

> 💡 **Never commit your real DB password.** Use environment variables in production.

### 7. Run Migrations

```bash
cd config
python manage.py migrate
```

### 8. Start the Server

```bash
python manage.py runserver
```

### 9. Open in Browser

```
http://127.0.0.1:8000/
```

---

## 🧪 Running Tests

Tests use **SQLite in-memory** — no XAMPP required.

```bash
cd config
python manage.py test portfolio --settings=config.test_settings --verbosity=2
```

**Expected:** `Ran 39 tests in ~0.1s   OK`

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stocks/` | List all supported stocks + prices |
| `GET` | `/api/portfolio/` | Get holdings and total investment |
| `POST` | `/api/portfolio/` | Add a holding `{"stock_symbol":"AAPL","quantity":5}` |
| `PATCH` | `/api/portfolio/<id>/` | Update quantity `{"quantity":10}` |
| `DELETE` | `/api/portfolio/<id>/` | Delete a holding |
| `GET` | `/api/portfolio/export/` | Download CSV |

---

## 📂 Project Structure

```
PythonProject1/
├── requirements.txt
├── .gitignore
└── config/                        ← Django root (run manage.py here)
    ├── manage.py
    ├── config/                    ← Settings package
    │   ├── settings.py
    │   ├── test_settings.py
    │   └── urls.py
    └── portfolio/                 ← Main app
        ├── stock_config.py        ← Centralized stock prices
        ├── models.py              ← PortfolioHolding model
        ├── views.py               ← All API views
        ├── urls.py                ← URL patterns
        ├── tests.py               ← 39 test cases
        ├── migrations/
        ├── templates/portfolio/index.html
        └── static/portfolio/
            ├── css/style.css
            └── js/app.js
```

---

## ✅ Acceptance Criteria

- [x] Stocks and prices displayed correctly
- [x] Add stocks with quantity
- [x] Investment value calculated server-side
- [x] Total portfolio investment correct
- [x] Duplicate stock → quantity merged (no duplicates)
- [x] Holdings viewable, editable, deletable
- [x] Invalid inputs rejected by backend
- [x] Client-supplied prices ignored
- [x] CSV export works
- [x] 39 / 39 tests pass

---

## 📄 License

This project is for educational / demonstration purposes.
