# ExpiryWise

ExpiryWise is a web app that tracks the expiry dates of food and household
products, warns you before they expire, reads dates from photos, and
suggests recipes to reduce waste.

## Features
- Add, edit, delete, search and filter products
- Status labels: Safe, Expiring Soon (5 days or fewer) and Expired
- Barcode lookup using the Open Food Facts database
- Expiry date reading from a photo using OCR (Tesseract)
- Recommendations and recipe ideas for items close to expiry
- Dashboard with counts by status and category
- Optional daily email reminders at 08:00

## Tech Stack
Python, Flask, SQLite, Pillow, pytesseract (Tesseract OCR), requests,
APScheduler, pytest, GitHub Actions

## Project Structure
```
ExpiryWise/
├── app.py               # routes, database access, validation
├── ocr.py               # reads the expiry date from an image
├── recommendation.py    # status labels and advice
├── recipes.py           # recipe ideas
├── reminders.py         # daily email reminders
├── error_handlers.py    # global error handlers
├── templates/           # HTML pages
├── tests/               # pytest tests
├── docs/TESTING.md      # testing and error handling guide
├── requirements.txt
└── .github/workflows/tests.yml
```

## Installation
```
git clone https://github.com/prasanthika2008-lgtm/ExpiryWise
cd ExpiryWise
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000 in your browser.

For OCR, install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
On Windows the default path `C:\Program Files\Tesseract-OCR\tesseract.exe`
is detected automatically.

## Configuration
| Variable | Purpose | Default |
|----------|---------|---------|
| EXPIRYWISE_DB | Database file path | database.db |
| FLASK_DEBUG | Set to 1 for debug mode | off |
| SMTP_USER, SMTP_PASS | Enable daily email reminders | disabled |

## API Endpoints
| Method | Endpoint | Description | Success | Errors |
|--------|----------|-------------|---------|--------|
| GET | `/` | Home page: product list with search and filters. Query params: `search`, `status`, `category`; `name`, `expiry_date`, `category`, `barcode` prefill the add form | 200 HTML | 500 |
| POST | `/` | Add a product. Form fields: `name`, `expiry_date`, `category`, `quantity`, `barcode` | 302 redirect to `/` | 200 HTML with message if validation fails |
| GET, POST | `/edit/<id>` | Show or save the edit form (name and expiry date). Unknown id redirects to `/` | 200 HTML / 302 | 200 HTML with message if validation fails |
| POST | `/delete/<id>` | Delete a product | 302 redirect to `/` | 405 if not POST |
| GET | `/scanner` | Scanner page (barcode and expiry photo) | 200 HTML | 500 |
| GET | `/dashboard` | Dashboard with counts and "use first" items | 200 HTML | 500 |
| GET | `/api/barcode/<code>` | Look up a 6-14 digit barcode | 200 JSON `{found, name, category}` | 400 invalid barcode, 502 service unavailable |
| POST | `/api/ocr` | Read an expiry date from an image (multipart field `image`) | 200 JSON `{expiry_date, raw_text}` | 400 no or unreadable image, 413 over 8 MB, 503 OCR not installed |
| GET | `/api/recipes/<product_name>` | Recipe ideas for a product | 200 JSON `{product, recipes}` | 500 |
| GET | `/api/stats` | Counts by status and category | 200 JSON `{total, by_status, by_category}` | 500 |

### Example: barcode lookup
```
GET /api/barcode/8901234567890
{"found": true, "name": "Brand Product", "category": "Packaged"}
```

### Example: stats
```
GET /api/stats
{"total": 5,
 "by_status": {"Safe": 3, "Expiring Soon": 1, "Expired": 1},
 "by_category": {"Dairy": 2, "Bakery": 3}}
```

## Database Schema
SQLite database with one table. It is created automatically on first run
by `create_table()`, which also adds missing columns to databases created
in Phase 1.

### Table: `products`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique product ID |
| name | TEXT | NOT NULL | Product name (1-100 characters) |
| expiry_date | TEXT | NOT NULL | Expiry date as `YYYY-MM-DD` |
| category | TEXT | DEFAULT 'Other' | Dairy, Meat, Fruits, Vegetables, Bakery, Packaged, Medicine or Other |
| quantity | INTEGER | DEFAULT 1 | Number of items (1-999) |
| barcode | TEXT | NULL allowed | Digits only, at most 14; NULL if missing or invalid |
| added_date | TEXT | NULL allowed | Date the product was added, `YYYY-MM-DD` |

`days_left`, `status` and `recommendation` are calculated when products are
loaded and are not stored in the database.

## Input Validation
| Field | Rule | If it fails |
|-------|------|-------------|
| name | Required, at most 100 characters | Error message, not saved |
| expiry_date | Valid date, year 2000-2100 | Error message, not saved |
| quantity | Whole number 1-999 | Error message, not saved |
| category | Must be in the category list | Becomes "Other" |
| barcode | Digits only, at most 14 | Set to NULL, product still saved |

## Testing
Run `pytest -v`. Full details are in [docs/TESTING.md](docs/TESTING.md).

## Screenshots
(Add 3 or 4 screenshots here: home page, scanner, dashboard.)

## Future Scope
- Mobile app version
- Push notifications
- Multi-user accounts
- Updating category, quantity and barcode from the edit page