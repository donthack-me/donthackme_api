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

import mongoengine as me


class Command(me.EmbeddedDocument):
    """Command Subdocument (Listed)."""

    timestamp = me.DateTimeField(required=True)
    command = me.StringField()
    success = me.BooleanField()


class Credentials(me.EmbeddedDocument):
    """Credential Subdocument."""

    username = me.StringField()
    password = me.StringField()
    success = me.BooleanField()
    timestamp = me.DateTimeField()


class Download(me.EmbeddedDocument):
    """Download Subdocument (Listed)."""

    timestamp = me.DateTimeField()
    realm = me.StringField()
    shasum = me.StringField()
    url = me.StringField()
    outfile = me.StringField()
    success = me.BooleanField()


class TtySize(me.EmbeddedDocument):
    """TTY Size Subdocument."""

    width = me.StringField()
    height = me.StringField()


class TtyLog(me.EmbeddedDocument):
    """TTY Log Subdocument."""

    size = me.StringField()
    ttylog = me.StringField()


class Session(me.Document):
    """Main Log Entry - Cowrie."""

    session = me.StringField(required=True)
    start_time = me.DateTimeField()
    end_time = me.DateTimeField()
    source_ip = me.StringField()
    sensor_ip = me.StringField()
    commands = me.EmbeddedDocumentListField(Command)
    credentials = me.EmbeddedDocumentListField(Credentials)
    downloads = me.EmbeddedDocumentListField(Download)
    ttylog = me.EmbeddedDocumentField(TtyLog)
    version = me.StringField()
    ttysize = me.EmbeddedDocumentField(TtySize)
    fingerprint = me.StringField()
    meta = {
        "indexes": [
            {
                "fields": ["session"],
                "unique": True
            },
            {"fields": ["source_ip"]},
            {"fields": ["sensor_ip"]},
            {"fields": ["start_time"]}
        ]
    }
