"""
test_error_handling.py
Tests that the global error handlers return the correct status
codes and JSON messages.
"""

import pytest
from flask import Flask, abort

from error_handlers import register_error_handlers


@pytest.fixture
def client():
    """Create a small Flask app with the error handlers attached."""
    test_app = Flask(__name__)
    test_app.config["TESTING"] = False
    test_app.config["PROPAGATE_EXCEPTIONS"] = False
    register_error_handlers(test_app)

    @test_app.route("/bad")
    def bad():
        abort(400)

    @test_app.route("/crash")
    def crash():
        raise RuntimeError("simulated crash")

    with test_app.test_client() as test_client:
        yield test_client


def test_unknown_route_returns_404(client):
    """An unknown URL should return 404 with a JSON error."""
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Resource not found"


def test_bad_request_returns_400(client):
    """An invalid request should return 400 with a JSON error."""
    response = client.get("/bad")
    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad request"


def test_server_crash_returns_500(client):
    """An unexpected exception should return 500 with a friendly message."""
    response = client.get("/crash")
    assert response.status_code == 500
    assert "Something went wrong" in response.get_json()["error"]