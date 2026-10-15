"""
error_handlers.py
Global error handlers for ExpiryWise.
Catches errors anywhere in the app and returns a clear JSON message
so users never see a crash page or a stack trace.
"""

from flask import jsonify


def register_error_handlers(app):
    """Attach the 400, 404 and 500 error handlers to a Flask app.

    Args:
        app: The Flask application object.
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Invalid request: missing or wrong data."""
        return jsonify(error="Bad request"), 400

    @app.errorhandler(404)
    def not_found(error):
        """The page or item does not exist."""
        return jsonify(error="Resource not found"), 404

    @app.errorhandler(500)
    def server_error(error):
        """Unexpected crash: show a friendly message instead."""
        return jsonify(error="Something went wrong. Please try again."), 500