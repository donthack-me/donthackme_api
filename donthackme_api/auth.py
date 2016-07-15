"""Authentication functions for cowrie API."""

from flask import request, jsonify  # , g
from functools import wraps


def check_auth(headers):
    """Return True when token is valid."""
    if "X-Auth-Token" in headers:
        return True
    return False


def requires_auth(f):
    """Decorate Flask Route to require LDAP Auth."""
    @wraps(f)
    def decorated(*args, **kwargs):
        headers = request.headers
        required_headers = ["X-Auth-Token"]

        if not all(x in headers for x in required_headers):
            err = "Required Headers: {0}"
            return jsonify(error=err.format(",".join(required_headers))), 401

        if not check_auth(headers):
            err = "Could not authenticate using those credentials"
            return jsonify(error=err), 403

        return f(*args, **kwargs)
    return decorated
