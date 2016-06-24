"""Database Models for Cowrie API."""
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

import json
import mongoengine as me


class Sensor(me.Document):
    """Register all Sensors."""

    timestamp = me.DateTimeField(required=True)
    ip = me.StringField(required=True)

    meta = {
        "indexes": [
            {"fields": ["ip"], "unique": True},
        ]
    }

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = self.to_mongo()

        response["timestamp"] = self.timestamp.isoformat()
        response.pop("_id", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class Command(me.Document):
    """Command Subdocument (Listed)."""

    session = me.ReferenceField('Session')
    timestamp = me.DateTimeField(required=True)
    command = me.StringField()
    success = me.BooleanField()

    meta = {
        "indexes": [
            {"fields": ["session"]},
            {"fields": ["command"]},
            {"fields": ["success"]},
            {"fields": ["timestamp"]}
        ]
    }

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = self.to_mongo()

        response["timestamp"] = self.timestamp.isoformat()
        response.pop("_id", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class Credentials(me.Document):
    """Credential Subdocument."""

    session = me.ReferenceField('Session')
    username = me.StringField()
    password = me.StringField()
    success = me.BooleanField()
    timestamp = me.DateTimeField()

    meta = {
        "indexes": [
            {"fields": ["session"]},
            {"fields": ["success"]},
            {"fields": ["username"]},
            {"fields": ["timestamp"]}
        ]
    }

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = self.to_mongo()

        response["timestamp"] = self.timestamp.isoformat()
        response.pop("_id", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class Fingerprint(me.Document):
    """Fingerprint Subdocument."""

    session = me.ReferenceField('Session')
    username = me.StringField()
    fingerprint = me.StringField()
    timestamp = me.DateTimeField()

    meta = {
        "indexes": [
            {"fields": ["session"]},
            {"fields": ["username"]},
            {"fields": ["timestamp"]}
        ]
    }

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = self.to_mongo()

        response["timestamp"] = self.timestamp.isoformat()
        response.pop("_id", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class Download(me.Document):
    """Download Subdocument (Listed)."""

    session = me.ReferenceField('Session')
    timestamp = me.DateTimeField()
    realm = me.StringField()
    shasum = me.StringField()
    url = me.StringField()
    outfile = me.StringField()

    meta = {
        "indexes": [
            {"fields": ["session"]},
            {"fields": ["success"]},
            {"fields": ["timestamp"]}
        ]
    }

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = self.to_mongo()

        response["timestamp"] = self.timestamp.isoformat()
        response.pop("_id", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class TtySize(me.EmbeddedDocument):
    """TTY Size Subdocument."""

    width = me.IntField()
    height = me.IntField()


class TtyLog(me.EmbeddedDocument):
    """TTY Log Subdocument."""

    size = me.StringField()
    log = me.StringField()


class Session(me.Document):
    """Main Log Entry - Cowrie."""

    session = me.StringField(required=True)
    start_time = me.DateTimeField()
    end_time = me.DateTimeField()
    source_ip = me.StringField()
    sensor_ip = me.StringField()
    ttylog = me.EmbeddedDocumentField(TtyLog)
    version = me.StringField()
    ttysize = me.EmbeddedDocumentField(TtySize)

    sensor = me.ReferenceField(Sensor)
    fingerprints = me.ListField(me.ReferenceField(Fingerprint))
    commands = me.ListField(me.ReferenceField(Command))
    credentials = me.ListField(me.ReferenceField(Credentials))
    downloads = me.ListField(me.ReferenceField(Download))

    meta = {
        "indexes": [
            {
                "fields": ["session", "sensor_ip"],
                "unique": Truecd""
            },
            {"fields": ["source_ip"]},
            {"fields": ["sensor_ip"]},
            {"fields": ["start_time"]}
        ]
    }

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = self.to_mongo()

        response["start_time"] = self.start_time.isoformat()
        if "end_time" in response:
            response["end_time"] = self.end_time.isoformat()
        response.pop("_id", None)

        response["sensor"] = self.sensor.to_dict()
        response["fingerprints"] = [item.to_dict() for
                                    item in self.fingerprints]
        response["commands"] = [item.to_dict() for
                                item in self.commands]
        response["credentials"] = [item.to_dict() for
                                   item in self.credentials]
        response["downloads"] = [item.to_dict() for
                                 item in self.downloads]

        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())
