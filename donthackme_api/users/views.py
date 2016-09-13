"""Events Blueprint for collecting data."""
# Copyright 2016 Russell Troxel
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from bson import objectid
from datetime import datetime, timedelta

from functools import wraps

from flask import request, jsonify, Blueprint, g, url_for, current_app

from donthackme_api.models import User
from donthackme_api.auth import requires_token

from mongoengine import errors


users = Blueprint('users', __name__, url_prefix="/users")


def user_action(f):
    """Decorate Flask Route to require Token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        return jsonify(args=args)
        args[0] = objectid.ObjectId(args[0])
        if not g.user.is_admin() and g.user.id != args[0]:
            err = "Only your own profile can be accessed."
            return jsonify(error=err), 403
        return f(*args, **kwargs)
    return decorated


@users.route("/new", methods=["POST"])
def create_user():
    """
    Create a new user.

    sample request:
    {
        "username": "new_user",
        "password": "secure_password",
        "email": "joe@google.com"
    }
    """
    payload = request.get_json(force=True)

    if not all(x in payload for x in ["username", "email", "password"]):
        err = "username, email, and password required to create a user."
        return jsonify(error=err), 400

    try:
        new_user = User(**payload).save()
    except errors.NotUniqueError:
        err = "User already exists with that name or email address."
        return jsonify(error=err), 409

    new_user.reload()
    g.user = new_user
    return_headers = {
        "Location": url_for(
            "users.get_user",
            user_id=new_user.id,
            _external=True)
    }
    return jsonify(user=new_user.to_dict()), 201, return_headers


@user_action
@users.route("/<string:user_id>", methods=["GET"])
@requires_token
def get_user(user_id):
    """
    Get user by id.

    returns:
    {
        "id": "user_id",
        "username": "username",
        "email": "joe@google.com",
        "api_key": "uuid"
    }
    """
    try:
        user = User.objects.get(id=user_id, deleted=0)
    except errors.DoesNotExist:
        err = "User {0} does not exist.".format(str(user_id))
        return jsonify(error=err), 404

    return jsonify(user=user.to_dict()), 200


@user_action
@users.route("/<string:user_id>", methods=["DELETE"])
@requires_token
def delete_user(user_id):
    """
    Delete User.

    returns:
        202 {"message": "Request to delete user <id> accepted."}
    """
    try:
        user = User.objects.get(id=user_id, deleted=0)
    except errors.DoesNotExist:
        err = "User {0} does not exist.".format(str(user_id))
        return jsonify(error=err), 404
    else:
        user.delete()
    msg = "Request to delete user {0} accepted.".format(str(user.id))
    return jsonify(message=msg), 202


@user_action
@users.route("/<string:user_id>", methods=["PUT"])
@requires_token
def update_user(user_id):
    """
    Update User.

    API Key is reset by passing an empty API key to put.
    username, email, password all require a new value.
    """
    payload = request.json
    allowed_to_edit = [
        "username",
        "email",
        "password",
        "api_key"
    ]
    for key in payload.keys():
        if key not in allowed_to_edit:
            err = "{0} cannot be edited.".format(key)
            return jsonify(error=err)

    try:
        user = User.objects.get(id=user_id, deleted=0)
    except errors.DoesNotExist:
        err = "User {0} does not exist.".format(str(user_id))
        return jsonify(error=err), 404

    if "api_key" in payload.keys():
        payload.pop("api_key")
        user.reset_api_key()

    if len(payload) > 0:
        user.update(**payload)

    user.save()
    user.reload()

    return jsonify(user=user.to_dict())


@users.route('/token')
def get_auth_token():
    """Generate and return Auth Token based on user/pass or api_key auth."""
    data = request.get_json(force=True)
    verified = False

    if "key_auth" in data:
        username = data["key_auth"].get("username")
        api_key = data["key_auth"].get("api_key")
        try:
            user = User.objects.get(
                username=username,
                api_key=api_key,
                deleted=0
            )
        except errors.DoesNotExist:
            pass
        else:
            verified = True

    elif "password_auth" in data:
        username = data["password_auth"].get("username")
        password = data["password_auth"].get("password")
        user = User.objects.get(username=username, deleted=0)
        verified = user.verify_password(password)
    if verified:
        g.user = user

        expires_in = current_app.config.get("DEFAULT_TOKEN_EXPIRATION", 14400)

        expires = datetime.utcnow() + timedelta(seconds=expires_in)
        token = g.user.generate_auth_token(expiration=expires_in)
        response = {
            "token": {
                "id": token.decode('ascii'),
                "expires": datetime.strftime(expires, "%Y-%m-%dT%H:%M:%S.%fZ")
            }
        }
        return jsonify(response)
    else:
        return jsonify({"message": "Forbidden."}), 403
