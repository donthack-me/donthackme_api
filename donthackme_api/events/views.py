"""Events Blueprint for collecting data."""
# Copyright (C) 2016 Russell Troxel

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from flask import request, jsonify, Blueprint, current_app

from mongoengine import errors

from donthackme_api import auth
from donthackme_api.models import (Sensor,
                                   Session,
                                   Credentials,
                                   Command,
                                   Download,
                                   Fingerprint,
                                   TransactionLog,
                                   TcpConnection)

import base64

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
@auth.requires_token
def session_connect():
    """Apply incoming log entry to session object in MongoEngine."""
    payload = request.get_json()
    sensor = get_or_insert_sensor(payload)
    try:
        session = Session(**payload)
        session.sensor = sensor
        session.save()

    except errors.NotUniqueError:
        msg = "Session {0} Already Exists".format(payload["session"])
        return jsonify(error=msg), 409
    return STANDARD_RESPONSE, 201


@events.route("/client/version", methods=["PUT"])
@events.route("/client/size", methods=["PUT"])
@auth.requires_token
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

    except errors.DoesNotExist:
        msg = "update_session: session {0} does not exist, inserting."
        current_app.logger.debug(msg.format(payload["session"]))

        session = Session(**payload)
        session.save()

    return STANDARD_RESPONSE, 202


@events.route("/session/closed", methods=["PUT"])
@auth.requires_token
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

    except errors.DoesNotExist:
        msg = "update_session: session {0} does not exist, inserting."
        current_app.logger.debug(msg.format(payload["session"]))

        session = Session(**payload)
        session.save()

    log_save(Session, session)
    return STANDARD_RESPONSE, 202


@events.route("/log/closed", methods=["PUT"])
@auth.requires_token
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
    return STANDARD_RESPONSE, 202


@events.route("/login/success", methods=["PUT"])
@events.route("/login/failed", methods=["PUT"])
@auth.requires_token
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

    creds = Credentials(**payload).save()
    log_save(Credentials, creds)
    session.update(push__credentials=creds)
    return STANDARD_RESPONSE, 202


@events.route("/command/success", methods=["PUT"])
@events.route("/command/failed", methods=["PUT"])
@auth.requires_token
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

    cmd = Command(**payload).save()
    log_save(Command, cmd)
    session.update(push__commands=cmd)
    return STANDARD_RESPONSE, 202


@events.route("/session/file_download", methods=["PUT"])
@auth.requires_token
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

    download = Download(**payload).save()
    log_save(Download, download)
    session.update(push__downloads=download)
    return STANDARD_RESPONSE, 202


@events.route("/client/fingerprint", methods=["PUT"])
@auth.requires_token
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

    fingerprint = Fingerprint.from_json(**payload).save()
    log_save(Fingerprint, fingerprint)
    session.update(push__fingerprints=fingerprint)
    return STANDARD_RESPONSE, 202


@events.route("/cdirect-tcpip/request", methods=["PUT"])
@auth.requires_token
def add_connection():
    """
    Process non-SSH connection.

    This includes:
        cowrie.direct-tcpip.request
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
    tcp = TcpConnection(**payload).save()
    log_save(TcpConnection, tcp)
    session.update(push__tcpconnections=tcp)
    session.reload()
    log_save(Session, session)
    return session.to_json(), 202
