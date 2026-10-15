"""
app.py
Main Flask application for ExpiryWise.

Responsibilities:
  - Database access (SQLite) and table creation
  - Validation of product input
  - Page routes: home (add/search/filter), edit, delete, scanner, dashboard
  - JSON API routes: barcode lookup, OCR, recipes, stats
  - Starting the optional daily email reminder scheduler

Other modules used:
  ocr.py             reads the expiry date from a photo
  recommendation.py  status labels and "what to do" advice
  recipes.py         recipe ideas for a product
  reminders.py       daily email summary
  error_handlers.py  global 400/404/405/413/500 handlers
"""

import os
import sqlite3
from datetime import date

import requests
from flask import Flask, jsonify, redirect, render_template, request

from error_handlers import register_error_handlers
from recipes import get_recipe_ideas
from recommendation import get_recommendation, get_status

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload limit
register_error_handlers(app)  # attach the global error handlers

# The database file can be overridden with an environment variable (used by tests).
DATABASE = os.environ.get("EXPIRYWISE_DB", "database.db")
CATEGORIES = ["Dairy", "Meat", "Fruits", "Vegetables", "Bakery", "Packaged", "Medicine", "Other"]
SOON_DAYS = 5  # a product is "Expiring Soon" when this many days or fewer remain
BARCODE_IGNORED_MESSAGE = "Product saved, but the barcode was invalid and was ignored."


# ---------------- DATABASE ----------------

def get_db():
    """Open a connection to the SQLite database.

    rows are returned as sqlite3.Row so columns can be read by name,
    for example row["name"].

    Returns:
        sqlite3.Connection: An open connection. The caller must close it.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    """Create the products table and add Phase 2 columns to older databases."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            expiry_date TEXT NOT NULL
        )
    """)
    # Databases created in Phase 1 only have id, name and expiry_date.
    # Look at the existing columns and add any Phase 2 column that is missing.
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(products)")}
    new_columns = {
        "category": "TEXT DEFAULT 'Other'",
        "quantity": "INTEGER DEFAULT 1",
        "barcode": "TEXT",
        "added_date": "TEXT",
    }
    for column, ddl in new_columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE products ADD COLUMN {column} {ddl}")
    conn.commit()
    conn.close()


# ---------------- VALIDATION ----------------

def validate_product(form):
    """Check and clean the product form data.

    Rules:
      - name: required, at most 100 characters
      - expiry_date: valid ISO date (YYYY-MM-DD), year between 2000 and 2100
      - category: must be in CATEGORIES, otherwise becomes "Other"
      - quantity: whole number from 1 to 999 (defaults to 1)
      - barcode: optional; digits only and at most 14 long, otherwise it is
        discarded (set to None) and the product is still saved

    Args:
        form: The submitted form data (request.form or any dict-like object).

    Returns:
        tuple: (clean_values, error). error is None when the input is valid.
        clean_values["barcode_ignored"] is True when a barcode was typed in
        but was invalid, so the caller can tell the user it was dropped.
    """
    name = (form.get("name") or "").strip()
    expiry_raw = (form.get("expiry_date") or "").strip()
    category = form.get("category") or "Other"
    barcode = (form.get("barcode") or "").strip() or None
    barcode_ignored = False

    if not name:
        return None, "Product name is required."
    if len(name) > 100:
        return None, "Product name must be 100 characters or fewer."
    try:
        expiry = date.fromisoformat(expiry_raw)
    except ValueError:
        return None, "Please enter a valid expiry date."
    if expiry.year < 2000 or expiry.year > 2100:
        return None, "Expiry date looks wrong. Please check the year."
    if category not in CATEGORIES:
        category = "Other"
    try:
        quantity = int(form.get("quantity") or 1)
    except ValueError:
        return None, "Quantity must be a whole number."
    if not 1 <= quantity <= 999:
        return None, "Quantity must be between 1 and 999."
    # An invalid barcode must not block saving, so just drop it.
    if barcode and (not barcode.isdigit() or len(barcode) > 14):
        barcode = None
        barcode_ignored = True

    return {
        "name": name,
        "expiry_date": expiry.isoformat(),
        "category": category,
        "quantity": quantity,
        "barcode": barcode,
        "barcode_ignored": barcode_ignored,
    }, None


# ---------------- PRODUCT PROCESSING ----------------

def get_products():
    """Load all products from the database and add calculated fields.

    For every product this adds days_left, status (Safe / Expiring Soon /
    Expired) and a recommendation message.

    Returns:
        list[dict]: Products sorted by expiry date, soonest first.
    """
    conn = get_db()
    rows = conn.execute("SELECT * FROM products ORDER BY expiry_date").fetchall()
    conn.close()

    products = []
    today = date.today()

    for row in rows:
        try:
            expiry = date.fromisoformat(row["expiry_date"])
        except ValueError:
            continue  # skip rows with a corrupted date instead of crashing
        days_left = (expiry - today).days  # negative means already expired
        category = row["category"] or "Other"
        products.append({
            "id": row["id"],
            "name": row["name"],
            "expiry_date": row["expiry_date"],
            "category": category,
            "quantity": row["quantity"] or 1,
            "barcode": row["barcode"],
            "days_left": days_left,
            "status": get_status(days_left, SOON_DAYS),
            "recommendation": get_recommendation(row["name"], days_left, category),
        })
    return products


# ---------------- HOME ----------------

@app.route("/", methods=["GET", "POST"])
def index():
    """Home page: add a product (POST) and list, search and filter products (GET).

    Query parameters (GET):
        search:   part of a product name
        status:   Safe, Expiring Soon or Expired
        category: one of CATEGORIES
        name, expiry_date, category, barcode: prefill the add form
        (used by the scanner page)
    """
    error = None
    saved_with_warning = False
    if request.method == "POST":
        values, error = validate_product(request.form)
        if values:
            conn = get_db()
            conn.execute(
                """INSERT INTO products
                   (name, expiry_date, category, quantity, barcode, added_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (values["name"], values["expiry_date"], values["category"],
                 values["quantity"], values["barcode"], date.today().isoformat()),
            )
            conn.commit()
            conn.close()
            if not values["barcode_ignored"]:
                return redirect("/")
            # Product was saved, but tell the user the barcode was dropped.
            saved_with_warning = True
            error = BARCODE_IGNORED_MESSAGE

    all_products = get_products()
    products = all_products

    # Apply the search box and the filter dropdowns.
    search = request.args.get("search", "").strip().lower()
    filter_status = request.args.get("status", "")
    filter_category = request.args.get("category", "")
    if search:
        products = [p for p in products if search in p["name"].lower()]
    if filter_status:
        products = [p for p in products if p["status"] == filter_status]
    if filter_category:
        products = [p for p in products if p["category"] == filter_category]

    # Values used to prefill the add form (e.g. from the scanner)
    if saved_with_warning:
        prefill = {"name": "", "expiry_date": "", "category": "", "barcode": ""}
    else:
        prefill = {
            "name": request.form.get("name") or request.args.get("name", ""),
            "expiry_date": request.form.get("expiry_date") or request.args.get("expiry_date", ""),
            "category": request.form.get("category") or request.args.get("category", ""),
            "barcode": request.form.get("barcode") or request.args.get("barcode", ""),
        }
    return render_template(
        "index.html",
        products=products,
        total=len(products),
        safe_count=sum(p["status"] == "Safe" for p in products),
        soon_count=sum(p["status"] == "Expiring Soon" for p in products),
        expired_count=sum(p["status"] == "Expired" for p in products),
        reminder_count=sum(p["status"] == "Expiring Soon" for p in all_products),
        categories=CATEGORIES,
        prefill=prefill,
        error=error,
    )


# ---------------- DELETE (POST only) ----------------

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    """Delete a product by id, then return to the home page.

    POST only, so a product cannot be deleted by just opening a link.
    """
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# ---------------- EDIT ----------------

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    """Show the edit form (GET) or save the changes (POST).

    If the product does not exist, the user is sent back to the home page.
    Only the name and expiry date are updated.
    """
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()

    if product is None:
        conn.close()
        return redirect("/")
    if request.method == "POST":
        values, error = validate_product(request.form)
        if error:
            conn.close()
            return render_template("edit.html", product=product, error=error)
        conn.execute(
            "UPDATE products SET name = ?, expiry_date = ? WHERE id = ?",
            (values["name"], values["expiry_date"], id),
        )
        conn.commit()
        conn.close()
        return redirect("/")
    conn.close()
    return render_template("edit.html", product=product, error=None)


# ---------------- SCANNER + BARCODE LOOKUP + OCR ----------------

@app.route("/scanner")
def scanner():
    """Page for scanning a barcode and photographing an expiry date."""
    return render_template("scanner.html", categories=CATEGORIES)


def map_category(raw):
    """Map an Open Food Facts category string onto one of our categories.

    Args:
        raw: Category text from Open Food Facts (may be None or empty).

    Returns:
        str: One of CATEGORIES. "Packaged" if text exists but nothing matches,
        "Other" if there is no text at all.
    """
    text = (raw or "").lower()
    rules = [
        ("Dairy", ("dairy", "milk", "cheese", "yogurt", "yoghurt", "butter", "curd")),
        ("Meat", ("meat", "chicken", "fish", "seafood", "egg")),
        ("Fruits", ("fruit",)),
        ("Vegetables", ("vegetable",)),
        ("Bakery", ("bread", "bakery", "biscuit", "cake")),
    ]
    for category, keywords in rules:
        if any(k in text for k in keywords):
            return category
    return "Packaged" if text else "Other"


@app.route("/api/barcode/<code>")
def barcode_lookup(code):
    """Look a barcode up on Open Food Facts and return the product name/category.

    Responses:
        200  {"found": true, "name": ..., "category": ...}
        200  {"found": false}                    barcode not in the database
        400  {"found": false, "error": ...}      barcode is not 6-14 digits
        502  {"found": false, "error": ...}      lookup service unreachable
    """
    # Reject anything that is not 6 to 14 digits before calling the network.
    if not code.isdigit() or not 6 <= len(code) <= 14:
        return jsonify({"found": False, "error": "Invalid barcode"}), 400
    try:
        response = requests.get(
            f"https://world.openfoodfacts.org/api/v2/product/{code}.json",
            params={"fields": "product_name,brands,categories"},
            headers={"User-Agent": "ExpiryWise/0.2 (student project)"},
            timeout=6,
        )
        data = response.json()
    except (requests.RequestException, ValueError):
        # No internet, timeout, or the service returned something that is not JSON.
        return jsonify({"found": False, "error": "Lookup service unavailable"}), 502
    if data.get("status") != 1:
        return jsonify({"found": False})

    product = data.get("product", {})
    name = (product.get("product_name") or "").strip()
    brand = (product.get("brands") or "").split(",")[0].strip()
    # Add the brand in front of the name unless the name already contains it.
    if brand and brand.lower() not in name.lower():
        name = f"{brand} {name}".strip()
    return jsonify({
        "found": bool(name),
        "name": name,
        "category": map_category(product.get("categories")),
    })


@app.route("/api/ocr", methods=["POST"])
def ocr_expiry():
    """Read an expiry date from an uploaded photo of the packaging.

    Expects a multipart form with a file field named "image".

    Responses:
        200  {"expiry_date": "YYYY-MM-DD" or null, "raw_text": ...}
        400  no image uploaded, or the image could not be read
        503  OCR (Tesseract) is not installed on the server
    """
    import ocr  # imported here so the app still starts without OCR libraries

    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"error": "No image uploaded"}), 400
    try:
        expiry, text = ocr.extract_expiry_date(file.stream)
    except RuntimeError:
        return jsonify({"error": "OCR is not installed on the server"}), 503
    except Exception:
        # Corrupted file, unsupported format, etc.
        return jsonify({"error": "Could not read that image"}), 400
    return jsonify({"expiry_date": expiry, "raw_text": text.strip()[:500]})


# ---------------- DASHBOARD + RECIPE IDEAS ----------------

@app.route("/dashboard")
def dashboard():
    """Dashboard page: counts by status and category, plus items to use first."""
    products = get_products()
    by_status = {"Safe": 0, "Expiring Soon": 0, "Expired": 0}
    by_category = {}
    for p in products:
        by_status[p["status"]] += 1
        by_category[p["category"]] = by_category.get(p["category"], 0) + 1

    # Items to use first: not yet expired, soonest first
    use_first = sorted(
        (p for p in products if p["days_left"] >= 0),
        key=lambda p: p["days_left"]
    )[:5]

    return render_template(
        "dashboard.html",
        total=len(products),
        by_status=by_status,
        by_category=by_category,
        use_first=use_first,
        waste_risk=by_status["Expiring Soon"] + by_status["Expired"],
    )


@app.route("/api/recipes/<path:product_name>")
def recipes(product_name):
    """Return recipe ideas for a product name as JSON.

    Response: {"product": <name>, "recipes": [...]}
    """
    return jsonify({"product": product_name, "recipes": get_recipe_ideas(product_name)})


# ---------------- STATS ----------------

@app.route("/api/stats")
def stats():
    """Return product counts as JSON: total, by status and by category."""
    products = get_products()
    by_status = {"Safe": 0, "Expiring Soon": 0, "Expired": 0}
    by_category = {}
    for p in products:
        by_status[p["status"]] += 1
        by_category[p["category"]] = by_category.get(p["category"], 0) + 1
    return jsonify({
        "total": len(products),
        "by_status": by_status,
        "by_category": by_category,
    })


# ---------------- START APP ----------------

def start_reminder_scheduler():
    """Send a daily summary email at 08:00 if SMTP credentials are configured.

    Needs the environment variables SMTP_USER and SMTP_PASS. Without them the
    scheduler is not started and the app runs normally.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    import reminders

    if not reminders.smtp_configured():
        print("Email reminders disabled (set SMTP_USER and SMTP_PASS to enable).")
        return
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: reminders.send_reminders(get_products()), "cron", hour=8)
    scheduler.start()
    print("Daily email reminders enabled (08:00).")


if __name__ == "__main__":
    create_table()
    start_reminder_scheduler()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", use_reloader=False)