"""Prototype API authentication guard.

For non-test execution the operator must configure a strong, random API token.
Token auth is intended for local development over localhost; use HTTPS, real
user accounts and role-based permissions before any campus deployment.
"""
import hmac
import os
from flask import jsonify, request

def install_api_guard(app):
    token = os.getenv("SMART_GATE_API_TOKEN", "")
    if not app.config.get("TESTING") and len(token) < 32:
        raise RuntimeError("Set SMART_GATE_API_TOKEN to a random token of at least 32 characters before starting the backend")

    @app.before_request
    def require_token():
        if not request.path.startswith("/api/") or request.path == "/api/health":
            return None
        if app.config.get("TESTING") and not token:
            return None
        supplied = request.headers.get("Authorization", "")
        expected = "Bearer " + token
        if not hmac.compare_digest(supplied.encode(), expected.encode()):
            return jsonify(error="authentication required"), 401
        return None

    @app.after_request
    def secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response
