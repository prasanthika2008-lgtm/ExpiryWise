from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
from recommendation import analyze_product

app = Flask(__name__)

DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# HOME / DASHBOARD
# =========================

@app.route("/", methods=["GET", "POST"])
def home():

    conn = get_db()

    if request.method == "POST":

        name = request.form["name"]
        expiry_date = request.form["expiry_date"]

        conn.execute(
            "INSERT INTO products (name, expiry_date) VALUES (?, ?)",
            (name, expiry_date)
        )

        conn.commit()

        conn.close()

        return redirect("/")


    rows = conn.execute(
        "SELECT id, name, expiry_date FROM products ORDER BY expiry_date"
    ).fetchall()


    products = []

    today = datetime.today().date()


    for row in rows:

        expiry = datetime.strptime(
            row["expiry_date"],
            "%Y-%m-%d"
        ).date()


        days_left = (expiry - today).days


        if days_left < 0:

            status = "Expired"

        elif days_left <= 5:

            status = "Expiring Soon"

        else:

            status = "Safe"


        recommendation = analyze_product(
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


    conn.close()


    return render_template(
        "index.html",
        products=products
    )


# =========================
# DELETE
# =========================

@app.route("/delete/<int:product_id>")
def delete_product(product_id):

    conn = get_db()


    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )


    conn.commit()

    conn.close()


    return redirect("/")


# =========================
# SCANNER PAGE
# =========================

@app.route("/scanner")
def scanner():

    return render_template("scanner.html")


# =========================
# ADD SCANNED PRODUCT
# =========================

@app.route("/scanner/add", methods=["POST"])
def add_scanned_product():

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


# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    app.run(debug=True)