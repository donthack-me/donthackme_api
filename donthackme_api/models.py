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
import uuid

import mongoengine as me

from bson import objectid
from datetime import datetime

from flask import current_app

from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


class User(me.Document):
    """User Document for Auth."""

    username = me.StringField(required=True)
    email = me.EmailField(required=True)
    password_hash = me.StringField(required=True)
    api_key = me.UUIDField(
        required=True,
        default=uuid.uuid4()
    )
    roles = me.ListField(
        me.StringField(),
        required=True,
        default=["user"]
    )
    version = me.IntField()
    deleted = me.DynamicField(required=True, default=0)
    deleted_at = me.DateTimeField()
    created_at = me.DateTimeField(
        required=True,
        default=datetime.utcnow()
    )
    updated_at = me.DateTimeField(
        required=True,
        default=datetime.utcnow()
    )

    meta = {
        "indexes": [
            {"fields": ["username", "deleted"], "unique": True},
            {"fields": ["email", "deleted"], "unique": True},
            {"fields": ["api_key", "deleted"], "unique": True},
        ]
    }

    def __init__(self, password=None, **kwargs):
        """init."""
        if password is not None:
            kwargs["password_hash"] = self.hash_password(password)
        super(User, self).__init__(**kwargs)

    def update(self, password=None, **kwargs):
        """Override Update Function."""
        if password is not None:
            kwargs["password_hash"] = self.hash_password(password)
        super(User, self).update(**kwargs)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        """Force updated_at on save."""
        document.updated_at = datetime.utcnow()

    def hash_password(self, password):
        """Create Hash from cleartext password."""
        return pwd_context.encrypt(password)

    def verify_password(self, password):
        """Verify password against hash."""
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=14400):
        """Generate a token for the user."""
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({
            'id': str(self.id)
        })

    @staticmethod
    def verify_auth_token(token):
        """Verify that a token is valid."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
            current_app.logger.info(data)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.objects(id=objectid.ObjectId(data['id'])).first()
        return user

    def reset_api_key(self):
        """Generate new API Key for account."""
        self.api_key = uuid.uuid4()

    def is_admin(self):
        """Test if admin."""
        if "admin" in self.roles:
            return True
        return False

    def is_user(self):
        """Test if user."""
        if "user" in self.roles:
            return True
        return False

    def delete(self):
        """Mark as deleted in the database."""
        self.deleted = str(self.id)
        self.deleted_at = datetime.utcnow()
        self.save()

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "api_key": self.api_key
        }
        return response

    def to_json(self):
        """Convert to json string."""
        return json.dumps(self.to_dict())


class TransactionLog(me.Document):
    """Capped Collection to Log transactions."""

    timestamp = me.DateTimeField(
        required=True,
        default=datetime.utcnow()
    )
    collection = me.StringField(required=True)
    doc_id = me.DynamicField()
    ts = me.SequenceField()

    meta = {"max_documents": 100000}


class Sensor(me.Document):
    """Register all Sensors."""

    timestamp = me.DateTimeField(required=True)
    name = me.StringField(required=True)
    ip = me.StringField()

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
    sensor_name = me.StringField()
    sensor_ip = me.StringField()
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
        response.pop("sensor_ip", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class Credentials(me.Document):
    """Credential Subdocument."""

    session = me.ReferenceField('Session')
    sensor_name = me.StringField()
    sensor_ip = me.StringField()
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
        response.pop("sensor_ip", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class Fingerprint(me.Document):
    """Fingerprint Subdocument."""

    session = me.ReferenceField('Session')
    sensor_name = me.StringField()
    sensor_ip = me.StringField()
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
        response.pop("sensor_ip", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class Download(me.Document):
    """Download Subdocument (Listed)."""

    session = me.ReferenceField('Session')
    sensor_name = me.StringField()
    sensor_ip = me.StringField()
    timestamp = me.DateTimeField()
    realm = me.StringField()
    shasum = me.StringField()
    url = me.StringField()
    outfile = me.StringField()

    meta = {
        "indexes": [
            {"fields": ["session"]},
            {"fields": ["timestamp"]}
        ]
    }

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = self.to_mongo()

        response["timestamp"] = self.timestamp.isoformat()
        response.pop("_id", None)
        response.pop("sensor_ip", None)
        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())


class TcpConnection(me.Document):
    """TcpConnection Subdocument (Listed)."""

    session = me.ReferenceField('Session')
    sensor_name = me.StringField()
    sensor_ip = me.StringField()
    timestamp = me.DateTimeField()
    dest_port = me.IntField()
    dest_ip = me.StringField()

    def to_dict(self):
        """Convert object to a sanitized python dictionary."""
        response = self.to_mongo()

        response["timestamp"] = self.timestamp.isoformat()
        response.pop("_id", None)
        response.pop("sensor_ip", None)
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

    size = me.IntField()
    log_location = me.StringField()
    log_binary = me.BinaryField()


class Session(me.Document):
    """Main Log Entry - Cowrie."""

    session = me.StringField(required=True)
    start_time = me.DateTimeField()
    end_time = me.DateTimeField()
    source_ip = me.StringField()
    sensor_name = me.StringField()
    sensor_ip = me.StringField()
    ttylog = me.EmbeddedDocumentField(TtyLog)
    ttysize = me.EmbeddedDocumentField(TtySize)

    ssh_version = me.StringField()
    ssh_kexAlgs = me.ListField(me.StringField())
    ssh_keyAlgs = me.ListField(me.StringField())
    ssh_macCS = me.ListField(me.StringField())

    sensor = me.ReferenceField(Sensor)
    fingerprints = me.ListField(me.ReferenceField(Fingerprint))
    commands = me.ListField(me.ReferenceField(Command))
    credentials = me.ListField(me.ReferenceField(Credentials))

    downloads = me.ListField(me.ReferenceField(Download))
    tcpconnections = me.ListField(me.ReferenceField(TcpConnection))

    meta = {
        "indexes": [
            {
                "fields": ["session", "sensor_ip"],
                "unique": True
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
        if "ttylog" in response:
            response["ttylog"].pop("log_binary", None)

        response["sensor"] = self.sensor.to_dict()
        response["fingerprints"] = [item.to_dict() for
                                    item in self.fingerprints]
        response["commands"] = [item.to_dict() for
                                item in self.commands]
        response["credentials"] = [item.to_dict() for
                                   item in self.credentials]
        response["downloads"] = [item.to_dict() for
                                 item in self.downloads]
        response["tcpconnections"] = [item.to_dict() for
                                      item in self.tcpconnections]

        return response

    def to_json(self):
        """Hijack class method to return our dict."""
        return json.dumps(self.to_dict())
