# ExpiryWise

**Smart food expiry tracking and food waste reduction system**

ExpiryWise is a Flask web app that tracks food and medicine expiry dates, warns you before items spoil,
fills in product details from a barcode, reads expiry dates from photos, and suggests how to use items
before they go to waste.

## Features

### Phase 1 (35%)
- Add, view, edit and delete products (CRUD)
- Remaining-days calculation and status: Safe / Expiring Soon / Expired
- Search and filter by status
- 5-day expiry window and rule-based recommendations

### Phase 2 (70%)
- **Extended data model:** category, quantity, barcode and added date (existing databases migrate automatically)
- **Barcode scanning with automatic product lookup** via the Open Food Facts API (name and category auto-filled)
- **OCR expiry-date extraction:** upload a photo of the package and the date is detected with Tesseract
  (handles formats like `15/03/2027`, `12 JAN 2027`, `03/2027`; picks the latest date when manufacture and expiry both appear)
- **Email reminders:** a daily 08:00 summary of items expiring soon or expired (APScheduler + SMTP)
- **Smarter recommendations:** category-aware tips and use-it-up ideas based on the product name
- **Category filter** and **statistics API** (`/api/stats`)
- **Input validation** and safe deletion (POST only)
- **Automated tests:** pytest suite covering CRUD, validation, barcode lookup, OCR parsing and reminders

## Architecture

```
Browser (HTML/CSS/JS, html5-qrcode)
        |
Flask app (app.py)
   |-- recommendation.py   status + recommendations
   |-- ocr.py              Tesseract OCR + date parsing
   |-- reminders.py        email summaries
   |-- Open Food Facts     barcode -> product lookup (external API)
        |
SQLite (database.db)
```

## Setup

```bash
git clone https://github.com/prasanthika2008-lgtm/ExpiryWise.git
cd ExpiryWise
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

OCR also needs the Tesseract program installed:
- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki and add it to PATH
- Ubuntu/Debian: `sudo apt install tesseract-ocr`
- macOS: `brew install tesseract`

Run the app:

```bash
python app.py
```

Open http://127.0.0.1:5000. (The camera scanner needs `localhost` or HTTPS.)

### Optional: email reminders

Set these environment variables before starting the app (use a Gmail *app password*, never your real password):

```
SMTP_USER=you@gmail.com
SMTP_PASS=your-app-password
REMINDER_TO=you@gmail.com      # optional, defaults to SMTP_USER
```

Test it once with `python reminders.py`.

## Tests

```bash
python -m pytest -q
```

## Roadmap (next phases)

- Dashboard charts and waste statistics
- User accounts
- LLM-powered recipe suggestions
- Push notifications / mobile app
- Cloud deployment and sync

## Author

Prasanthika M, BE CSE, 2nd Year
