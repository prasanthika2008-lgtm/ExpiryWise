"""
test_error_handling.py
Tests for the global error handlers.

Part 1 uses a small throwaway Flask app to trigger errors on purpose.
Part 2 sends bad requests to the real ExpiryWise app. None of these
touch the database or the internet.
"""

import pytest
from flask import Flask, abort, request

from app import app as real_app
from error_handlers import register_error_handlers


# ---------- Part 1: throwaway app ----------

@pytest.fixture
def client():
    """A tiny Flask app with the error handlers and some routes that fail."""
    test_app = Flask(__name__)
    test_app.config["PROPAGATE_EXCEPTIONS"] = False  # let the 500 handler run
    test_app.config["MAX_CONTENT_LENGTH"] = 100      # tiny limit to trigger 413
    register_error_handlers(test_app)

    @test_app.route("/bad")
    def bad():
        abort(400)

    @test_app.route("/crash")
    def crash():
        raise RuntimeError("simulated crash")

    @test_app.route("/upload", methods=["POST"])
    def upload():
        request.get_data()  # reading the body triggers the size check
        return "ok"

    with test_app.test_client() as test_client:
        yield test_client


def test_unknown_route_returns_404(client):
    """An unknown URL returns 404 with a JSON error."""
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Resource not found"


def test_bad_request_returns_400(client):
    """An invalid request returns 400 with a JSON error."""
    response = client.get("/bad")
    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad request"


def test_wrong_method_returns_405(client):
    """Using GET on a POST-only URL returns 405."""
    response = client.get("/upload")
    assert response.status_code == 405
    assert response.get_json()["error"] == "Method not allowed"


def test_upload_too_large_returns_413(client):
    """A body bigger than MAX_CONTENT_LENGTH returns 413."""
    response = client.post("/upload", data=b"x" * 1000)
    assert response.status_code == 413
    assert "too large" in response.get_json()["error"].lower()


def test_server_crash_returns_500(client):
    """An unexpected exception returns 500 with a friendly message."""
    response = client.get("/crash")
    assert response.status_code == 500
    assert "Something went wrong" in response.get_json()["error"]


# ---------- Part 2: the real ExpiryWise app ----------

@pytest.fixture
def real_client():
    """Test client for the real app."""
    real_app.config["TESTING"] = True
    with real_app.test_client() as test_client:
        yield test_client


def test_real_app_unknown_route_404(real_client):
    """The real app returns the JSON 404 for an unknown URL."""
    response = real_client.get("/nope")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Resource not found"


def test_real_app_delete_requires_post(real_client):
    """/delete/<id> is POST only, so GET must return 405."""
    response = real_client.get("/delete/1")
    assert response.status_code == 405


def test_invalid_barcode_lookup_returns_400(real_client):
    """A non-numeric barcode is rejected before any network call."""
    response = real_client.get("/api/barcode/abc")
    assert response.status_code == 400
    assert response.get_json()["found"] is False


def test_ocr_without_image_returns_400(real_client):
    """Calling /api/ocr with no file returns 400."""
    response = real_client.post("/api/ocr")
    assert response.status_code == 400
    assert response.get_json()["error"] == "No image uploaded"