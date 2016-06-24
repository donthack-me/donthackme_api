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

from flask import request, jsonify, Blueprint

from mongoengine import errors

from cowrie_api import auth
from cowrie_api.models import (Sensor,
                               Session,
                               Credentials,
                               Command,
                               Download,
                               Fingerprint)

import json

events = Blueprint('events', __name__, url_prefix="/events")


@events.route("/session/connect", methods=["POST"])
@auth.requires_auth
def session_connect():
    """Apply incoming log entry to session object in MongoEngine."""
    payload = request.get_json()
    try:
        Sensor(
            ip=payload["sensor_ip"],
            timestamp=payload["start_time"]
        ).save()
    except errors.NotUniqueError:
        pass

    try:
        sensor = Sensor.objects.get(ip=payload["sensor_ip"])
        session = Session.from_json(json.dumps(payload))
        session.sensor = sensor
        session.save()
    except errors.NotUniqueError:
        msg = "Session {0} Already Exists".format(payload["session"])
        return jsonify(error=msg), 409
    session.reload()
    return session.to_json()


@events.route("/client/version", methods=["PUT"])
@events.route("/client/size", methods=["PUT"])
@events.route("/log/closed", methods=["PUT"])
@events.route("/session/closed", methods=["PUT"])
@auth.requires_auth
def update_session():
    """
    Process events which require normal, atomic updates.

    This includes:
        cowrie.client.version
        cowrie.client.size
        cowrie.log.closed
        cowrie.session.closed
    """
    payload = request.get_json()
    try:
        session = Session.objects.get(session=payload["session"])
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    session.update(**payload)
    session.reload()
    return session.to_json()


@events.route("/login/success", methods=["PUT"])
@events.route("/login/failed", methods=["PUT"])
@auth.requires_auth
def add_login_attempt():
    """
    Process login attempts.

    This includes:
        cowrie.login.success
        cowrie.login.failed
    """
    payload = request.get_json()
    try:
        session = Session.objects.get(
            session=payload["session"],
            sensor=payload["sensor_ip"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    creds = Credentials.from_json(json.dumps(payload)).save()
    session.update(push__credentials=creds)
    session.reload()
    return session.to_json()


@events.route("/command/success", methods=["PUT"])
@events.route("/command/failed", methods=["PUT"])
@auth.requires_auth
def add_command():
    """
    Process Honeypot Commands.

    This includes:
        cowrie.command.success
        cowrie.command.failed
    """
    payload = request.get_json()
    try:
        session = Session.objects.get(
            session=payload["session"],
            sensor=payload["sensor_ip"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    cmd = Command.from_json(json.dumps(payload)).save()
    session.update(push__commands=cmd)
    session.reload()
    return session.to_json()


@events.route("/session/file_download", methods=["PUT"])
@auth.requires_auth
def add_download():
    """
    Process Downloads.

    This includes:
        cowrie.session.file_download
    """
    payload = request.get_json()
    try:
        session = Session.objects.get(
            session=payload["session"],
            sensor=payload["sensor_ip"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    download = Download.from_json(json.dumps(payload)).save()
    session.update(push__downloads=download)
    session.reload()
    return session.to_json()


@events.route("/client/fingerprint", methods=["PUT"])
@auth.requires_auth
def add_fingerprint():
    """
    Process Downloads.

    This includes:
        cowrie.client.fingerprint
    """
    payload = request.get_json()
    try:
        session = Session.objects.get(
            session=payload["session"],
            sensor=payload["sensor_ip"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    fingerprint = Fingerprint.from_json(json.dumps(payload)).save()
    session.update(push__fingerprints=fingerprint)
    session.reload()
    return session.to_json()
