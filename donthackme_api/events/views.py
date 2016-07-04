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

from flask import request, jsonify, Blueprint, current_app

from mongoengine import errors

from donthackme_api import auth
from donthackme_api.models import (Sensor,
                                   Session,
                                   Credentials,
                                   Command,
                                   Download,
                                   Fingerprint,
                                   TransactionLog)

import base64
import json

events = Blueprint('events', __name__, url_prefix="/events")

STANDARD_RESPONSE = '{"acknowledged": true}'


def log_save(doc_class, doc_instance):
    """Report document change to capped collection."""
    TransactionLog(
        collection=doc_class._get_collection_name(),
        doc_id=doc_instance.id
    ).save()


def get_or_insert_sensor(payload):
    """Insert Sensor if doesn't exist."""
    try:
        sensor = Sensor(
            name=payload["sensor_name"],
            ip=payload["sensor_ip"],
            timestamp=payload["start_time"]
        ).save()
        log_save(Sensor, sensor)
        return sensor
    except errors.NotUniqueError:
        sensor = Sensor.objects.get(
            name=payload["sensor_name"],
            ip=payload["sensor_ip"]
        )
        return sensor


@events.route("/session/connect", methods=["POST"])
@auth.requires_auth
def session_connect():
    """Apply incoming log entry to session object in MongoEngine."""
    payload = request.get_json()
    sensor = get_or_insert_sensor(payload)
    try:
        session = Session.from_json(json.dumps(payload))
        session.sensor = sensor
        session.save()

    except errors.NotUniqueError:
        msg = "Session {0} Already Exists".format(payload["session"])
        return jsonify(error=msg), 409
    session.reload()
    return STANDARD_RESPONSE, 201


@events.route("/client/version", methods=["PUT"])
@events.route("/client/size", methods=["PUT"])
@auth.requires_auth
def update_session():
    """
    Process events which require normal, atomic updates.

    This includes:
        cowrie.client.version
        cowrie.client.size
    """
    payload = request.get_json()

    try:
        session = Session.objects.get(
            session=payload["session"],
            sensor_name=payload["sensor_name"]
        )
        session.update(**payload)
        session.reload()

    except errors.DoesNotExist:
        msg = "update_session: session {0} does not exist, inserting."
        current_app.logger.debug(msg.format(payload["session"]))

        session = Session.from_json(json.dumps(payload))
        session.save()

    return STANDARD_RESPONSE, 202


@events.route("/session/closed", methods=["PUT"])
@auth.requires_auth
def close_session():
    """
    Process events which require normal, atomic updates.

    This includes:
        cowrie.session.closed
    """
    payload = request.get_json()

    try:
        session = Session.objects.get(
            session=payload["session"],
            sensor_name=payload["sensor_name"]
        )
        session.update(**payload)
        session.reload()

    except errors.DoesNotExist:
        msg = "update_session: session {0} does not exist, inserting."
        current_app.logger.debug(msg.format(payload["session"]))

        session = Session.from_json(json.dumps(payload))
        session.save()

    log_save(Session, session)
    return STANDARD_RESPONSE, 202


@events.route("/log/closed", methods=["PUT"])
@auth.requires_auth
def close_ttylog():
    """
    Process log closure.

    This processing is special as it requires the decoding of
    the binary log file before insertion.

    This includes:
        cowrie.log.closed
    """
    payload = request.get_json()

    try:
        session = Session.objects.get(
            session=payload["session"],
            sensor_name=payload["sensor_name"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    b64_ttylog = payload["ttylog"].pop("log_base64")
    payload["ttylog"]["log_binary"] = base64.b64decode(b64_ttylog)
    session.update(**payload)
    session.reload()
    return STANDARD_RESPONSE, 202


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
            sensor_name=payload["sensor_name"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    creds = Credentials.from_json(json.dumps(payload)).save()
    log_save(Credentials, creds)
    session.update(push__credentials=creds)
    session.reload()
    return STANDARD_RESPONSE, 202


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
            sensor_name=payload["sensor_name"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    cmd = Command.from_json(json.dumps(payload)).save()
    log_save(Command, cmd)
    session.update(push__commands=cmd)
    session.reload()
    return STANDARD_RESPONSE, 202


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
            sensor_name=payload["sensor_name"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    download = Download.from_json(json.dumps(payload)).save()
    log_save(Download, download)
    session.update(push__downloads=download)
    session.reload()
    return STANDARD_RESPONSE, 202


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
            sensor_name=payload["sensor_name"]
        )
    except errors.DoesNotExist:
        msg = "Session {0} Not Found.".format(payload["session"])
        return jsonify(error=msg), 404

    fingerprint = Fingerprint.from_json(json.dumps(payload)).save()
    log_save(Fingerprint, fingerprint)
    session.update(push__fingerprints=fingerprint)
    session.reload()
    return STANDARD_RESPONSE, 202


@events.route("/cdirect-tcpip/request", methods=["PUT"])
def add_connection():
    """
    Process non-SSH connection.

    This includes:
        cowrie.direct-tcpip.request
    """
    # payload = request.get_json()
    # try:
    #     session = Session.objects.get(
    #         session=payload["session"],
    #         sensor_name=payload["sensor_name"]
    #     )
    # except errors.DoesNotExist:
    #     msg = "Session {0} Not Found.".format(payload["session"])
    #     return jsonify(error=msg), 404
    # tcp = TcpConnection.from_json(json.dumps(payload)).save()
    # log_save(TcpConnection, tcp)
    # session.update(push__tcpconnections=tcp)
    # session.reload()
    # log_save(Session, session)
    # return session.to_json(), 202
    return '{"msg": "no longer implemented."}', 202
