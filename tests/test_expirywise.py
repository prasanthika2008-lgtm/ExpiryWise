import io
import os
import sys
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as expiry_app
import ocr
import recommendation
import reminders


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(expiry_app, "DATABASE", str(tmp_path / "test.db"))
    expiry_app.create_table()
    expiry_app.app.config["TESTING"] = True
    return expiry_app.app.test_client()


def add(client, name, days, **extra):
    data = {"name": name, "expiry_date": (date.today() + timedelta(days=days)).isoformat()}
    data.update(extra)
    return client.post("/", data=data, follow_redirects=True)


# ---------- status + recommendations ----------
def test_status_boundaries():
    assert recommendation.get_status(-1) == "Expired"
    assert recommendation.get_status(0) == "Expiring Soon"
    assert recommendation.get_status(5) == "Expiring Soon"
    assert recommendation.get_status(6) == "Safe"


def test_recommendations_use_category_and_name():
    assert "expired" in recommendation.get_recommendation("Milk", -2).lower()
    assert "today" in recommendation.get_recommendation("Bread", 0).lower()
    assert "tea" in recommendation.get_recommendation("Milk", 20).lower()
    assert "freeze" in recommendation.get_recommendation("Chicken curry", 20, "Meat").lower() \
        or "frozen" in recommendation.get_recommendation("Chicken curry", 20, "Meat").lower()
    assert "dispose" in recommendation.get_recommendation("Paracetamol", -1, "Medicine").lower()


# ---------- CRUD + validation ----------
def test_add_and_list_product(client):
    r = add(client, "Milk", 3, category="Dairy", quantity="2")
    assert b"Milk" in r.data and b"Dairy" in r.data


def test_rejects_bad_input(client):
    assert b"valid expiry date" in client.post("/", data={"name": "X", "expiry_date": "nope"}).data
    assert b"name is required" in client.post("/", data={"name": " ", "expiry_date": "2030-01-01"}).data
    assert b"between 1 and 999" in client.post(
        "/", data={"name": "X", "expiry_date": "2030-01-01", "quantity": "0"}).data


def test_delete_requires_post(client):
    add(client, "Curd", 4)
    assert client.get("/delete/1").status_code == 405       # GET no longer deletes
    client.post("/delete/1")
    assert b"Curd" not in client.get("/").data


def test_edit_product(client):
    add(client, "Rice", 10)
    new_date = (date.today() + timedelta(days=30)).isoformat()
    client.post("/edit/1", data={"name": "Basmati Rice", "expiry_date": new_date})
    assert b"Basmati Rice" in client.get("/").data


def test_search_and_filters(client):
    add(client, "Milk", 2, category="Dairy")
    add(client, "Old Bread", -3, category="Bakery")
    assert b"Old Bread" not in client.get("/?status=Expiring Soon").data
    assert b"Old Bread" in client.get("/?status=Expired").data
    assert b"Milk" not in client.get("/?category=Bakery").data
    assert b"Milk" in client.get("/?search=mil").data


def test_corrupted_date_does_not_crash(client):
    conn = expiry_app.get_db()
    conn.execute("INSERT INTO products (name, expiry_date) VALUES ('Bad', 'garbage')")
    conn.commit(); conn.close()
    assert client.get("/").status_code == 200


def test_stats_endpoint(client):
    add(client, "Milk", 2, category="Dairy")
    add(client, "Bread", -1, category="Bakery")
    data = client.get("/api/stats").get_json()
    assert data["total"] == 2
    assert data["by_status"]["Expired"] == 1


# ---------- barcode lookup ----------
class FakeResponse:
    def __init__(self, payload): self._p = payload
    def json(self): return self._p


def test_barcode_found(client):
    payload = {"status": 1, "product": {"product_name": "Choco Spread", "brands": "Nutty",
                                        "categories": "Spreads, Sweet"}}
    with patch("app.requests.get", return_value=FakeResponse(payload)):
        data = client.get("/api/barcode/8901234567890").get_json()
    assert data["found"] and data["name"] == "Nutty Choco Spread" and data["category"] == "Packaged"


def test_barcode_not_found_and_invalid(client):
    with patch("app.requests.get", return_value=FakeResponse({"status": 0})):
        assert client.get("/api/barcode/8901234567890").get_json()["found"] is False
    assert client.get("/api/barcode/abc").status_code == 400


def test_barcode_service_down(client):
    import requests
    with patch("app.requests.get", side_effect=requests.ConnectionError):
        assert client.get("/api/barcode/8901234567890").status_code == 502


# ---------- OCR ----------
@pytest.mark.parametrize("text,expected", [
    ("MFG 01/01/2026  EXP 15/03/2027", "2027-03-15"),
    ("BEST BEFORE 12 JAN 2027", "2027-01-12"),
    ("USE BY 03/2027", "2027-03-31"),
    ("EXP: 20.08.27", "2027-08-20"),
    ("no date here", None),
])
def test_parse_expiry_date(text, expected):
    assert ocr.parse_expiry_date(text) == expected


def test_ocr_endpoint_reads_image(client):
    img = Image.new("RGB", (900, 220), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
    except OSError:
        pytest.skip("font not available")
    draw.text((30, 60), "EXP 15/03/2027", fill="black", font=font)
    buf = io.BytesIO(); img.save(buf, "PNG"); buf.seek(0)
    r = client.post("/api/ocr", data={"image": (buf, "label.png")}, content_type="multipart/form-data")
    assert r.get_json()["expiry_date"] == "2027-03-15"


def test_ocr_requires_image(client):
    assert client.post("/api/ocr").status_code == 400


# ---------- reminders ----------
def test_reminder_message_content():
    products = [
        {"name": "Milk", "days_left": 2, "expiry_date": "2026-10-11", "status": "Expiring Soon"},
        {"name": "Bread", "days_left": -1, "expiry_date": "2026-10-08", "status": "Expired"},
        {"name": "Rice", "days_left": 90, "expiry_date": "2027-01-01", "status": "Safe"},
    ]
    subject, body = reminders.build_message(products)
    assert "1 expiring soon, 1 expired" in subject
    assert "Milk" in body and "Bread" in body and "Rice" not in body


def test_no_reminder_when_all_safe():
    assert reminders.build_message([{"name": "Rice", "days_left": 90, "expiry_date": "x", "status": "Safe"}]) is None


def test_send_skips_without_smtp(monkeypatch):
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)
    soon = [{"name": "Milk", "days_left": 1, "expiry_date": "x", "status": "Expiring Soon"}]
    assert reminders.send_reminders(soon) is False
