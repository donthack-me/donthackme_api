"""Authentication functions for cowrie API."""

from flask import request, jsonify, g
from functools import wraps

from models import User

from mongoengine import errors


def check_auth(headers):
    """Return True when token is valid."""
    if "X-JWT" in headers:
        user = User.verify_auth_token(headers["X-JWT"])
        if user is not None:
            g.user = user
            return True
    elif "X-Auth-Token" in headers:
        try:
            user = User.objects.get(
                api_key=headers["X-Auth-Token"],
                version=1,
                deleted=0
            )
        except errors.DoesNotExist:
            return False
        else:
            g.user = user
            return True
    return False


def requires_token(f):
    """Decorate Flask Route to require Token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        headers = request.headers
        required_headers = ["X-Auth-Token", "X-JWT"]

        if not any(x in headers for x in required_headers):
            err = "Required Headers: {0}"
            return jsonify(error=err.format(",".join(required_headers))), 401

        if not check_auth(headers):
            err = "Could not authenticate using those credentials"
            return jsonify(error=err), 403

        return f(*args, **kwargs)
    return decorated
