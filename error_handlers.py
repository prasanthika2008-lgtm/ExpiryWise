"""
error_handlers.py
Global error handlers for ExpiryWise.

Catches errors anywhere in the app and returns a clear JSON message,
so users never see a crash page or a stack trace.
"""

from flask import jsonify


def register_error_handlers(app):
    """Attach the global error handlers to a Flask app.

    Handled errors: 400 (bad request), 404 (not found),
    405 (wrong HTTP method), 413 (upload too large), 500 (server crash).

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

    @app.errorhandler(405)
    def method_not_allowed(error):
        """The URL exists but does not accept this HTTP method."""
        return jsonify(error="Method not allowed"), 405

    @app.errorhandler(413)
    def too_large(error):
        """Uploaded file is bigger than MAX_CONTENT_LENGTH (8 MB)."""
        return jsonify(error="File too large (maximum 8 MB)"), 413

    @app.errorhandler(500)
    def server_error(error):
        """Unexpected crash: show a friendly message instead of a traceback."""
        return jsonify(error="Something went wrong. Please try again."), 500