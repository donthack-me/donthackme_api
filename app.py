"""Cowrie Frontend API for collecting log data."""
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

# 'cowrie.session.connect'
# 'cowrie.login.success'
# 'cowrie.login.failed'
# 'cowrie.command.success'
# 'cowrie.command.failed'
# 'cowrie.session.file_download'
# 'cowrie.client.version'
# 'cowrie.client.size'
# 'cowrie.session.closed'
# 'cowrie.log.closed'
# 'cowrie.client.fingerprint'

from flask import Flask, request, jsonify

import mongoengine as me
from mongoengine import errors

import json

from cowrie_api import auth
from cowrie_api.models import (Session,
                               Credentials,
                               Command,
                               Download)


app = Flask(__name__)
app.config.from_object('cowrie_api.default_config')
try:
    app.config.from_envvar('COWRIE_API_SETTINGS')
except:
    pass

VERSION = app.config.get("API_VERSION")

me.connect(
    app.config.get("MONGO_DB"),
    host=app.config.get("MONGO_HOST"),
    port=app.config.get("MONGO_PORT"),
    username=app.config.get("MONGO_USER"),
    password=app.config.get("MONGO_PASS"),
)


@app.route("/{0}/log".format(VERSION), methods=["POST"])
@auth.requires_auth
def log_entry():
    """Apply incoming log entry to session object in MongoEngine."""
    entry = request.get_json()

    if entry["eventid"] == "cowrie.session.connect":
        session = Session.from_json(json.dumps(entry["payload"])).save()
        return session.to_json()
    else:
        try:
            session = Session.objects.get(session=entry["payload"]["session"])
        except errors.DoesNotExist:
            msg = "Session {0} Not Found.".format(entry["payload"]["session"])
            return jsonify(error=msg), 404

        if entry["eventid"] in ['cowrie.client.version',
                                'cowrie.client.size'
                                'cowrie.session.closed',
                                'cowrie.log.closed',
                                'cowrie.client.fingerprint']:
            session.update(**entry["payload"])
            session.reload()
            return session.to_json()

        elif entry["eventid"] in ['cowrie.login.success',
                                  'cowrie.login.failed']:

            session = Session.objects.get(session=entry["payload"]["session"])
            creds = json.dumps(entry["payload"]["credential"])
            creds = Credentials.from_json(creds)
            session.update(push__credentials=creds)
            session.reload()
            return session.to_json()

        elif entry["eventid"] in['cowrie.command.success',
                                 'cowrie.command.failed']:

            session = Session.objects.get(session=entry["payload"]["session"])
            cmd = json.dumps(entry["payload"]["command"])
            cmd = Command.from_json(cmd)
            session.update(push__commands=cmd)
            session.reload()
            return session.to_json()

        elif entry["eventid"] == 'cowrie.session.file_download':

            session = Session.objects(session=entry["payload"]["session"])
            download = json.dumps(entry["payload"]["download"])
            download = Download.from_json(download)
            session.update(push__downloads=download)
            session.reload()
            return session.to_json()

        else:
            msg = "eventid type {0} not recognized.".format(entry["eventid"])
            return jsonify(error=msg), 422

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

{
    "eventid": "eventid",
    "payload": {
        "session": "string",
        "start_time": "datetime",
        "source_ip": "string",
        "sensor_ip": "string",
        "commands": [
            {
                "timestamp": "datetime",
                "command": "string",
                "success": "boolean"
            }
        ],
        "loggedin": "boolean",
        "end_time": "datetime",
        "credentials": {
            "username": "string",
            "password": "string"
        },
        "downloads": [
            {
                "timestamp": "datetime",
                "realm": "string",
                "shasum": "string",
                "url": "string",
                "outfile": "string",
                "success": "boolean"
            }
        ],
        "ttylog": {
            "size": "string",
            "ttylog": "string"
        },
        "version": "string",
        "ttysize": {
            "width": "string",
            "height": "string"
        },
        "fingerprint": "string"
    }
}
