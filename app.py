from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date

from recommendation import get_recommendation


app = Flask(__name__)

DATABASE = "database.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            expiry_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- PRODUCT PROCESSING ----------------

def get_products():

    conn = get_db()

    rows = conn.execute(
        "SELECT * FROM products ORDER BY expiry_date"
    ).fetchall()

    conn.close()

    products = []

    today = date.today()

    for row in rows:

        expiry = date.fromisoformat(row["expiry_date"])

        days_left = (expiry - today).days

        if days_left < 0:
            status = "Expired"

        elif days_left <= 5:
            status = "Expiring Soon"

        else:
            status = "Safe"

        recommendation = get_recommendation(
            row["name"],
            days_left
        )

        products.append({
            "id": row["id"],
            "name": row["name"],
            "expiry_date": row["expiry_date"],
            "days_left": days_left,
            "status": status,
            "recommendation": recommendation
        })

    return products


# ---------------- HOME ----------------

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        name = request.form["name"]
        expiry_date = request.form["expiry_date"]

        conn = get_db()

        conn.execute(
            "INSERT INTO products (name, expiry_date) VALUES (?, ?)",
            (name, expiry_date)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    products = get_products()

    search = request.args.get("search", "").strip().lower()
    filter_status = request.args.get("status", "")

    if search:
        products = [
            p for p in products
            if search in p["name"].lower()
        ]

    if filter_status:
        products = [
            p for p in products
            if p["status"] == filter_status
        ]

    total = len(products)

    safe_count = len([
        p for p in products
        if p["status"] == "Safe"
    ])

    soon_count = len([
        p for p in products
        if p["status"] == "Expiring Soon"
    ])

    expired_count = len([
        p for p in products
        if p["status"] == "Expired"
    ])

    return render_template(
        "index.html",
        products=products,
        total=total,
        safe_count=safe_count,
        soon_count=soon_count,
        expired_count=expired_count
    )


# ---------------- DELETE ----------------

@app.route("/delete/<int:id>")
def delete(id):

    conn = get_db()

    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# ---------------- EDIT ----------------

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    conn = get_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (id,)
    ).fetchone()

    if product is None:

        conn.close()

        return redirect("/")

    if request.method == "POST":

        name = request.form["name"]
        expiry_date = request.form["expiry_date"]

        conn.execute(
            """
            UPDATE products
            SET name = ?, expiry_date = ?
            WHERE id = ?
            """,
            (name, expiry_date, id)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    conn.close()

    return render_template(
        "edit.html",
        product=product
    )


# ---------------- SCANNER ----------------

@app.route("/scanner")
def scanner():

    return render_template("scanner.html")


# ---------------- START APP ----------------

if __name__ == "__main__":

    create_table()

    app.run(
        debug=True
    )