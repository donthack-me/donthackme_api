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

from flask import Flask

from flask_mongoengine import MongoEngine

from donthackme_api.events.views import events
from donthackme_api.admin.views import admin

DEFAULT_BLUEPRINTS = [
    events,
    admin
]


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""
    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_app(app):
    """Retrieve App Configuration."""
    app.config.from_object('donthackme_api.default_config')
    print("doin it...")
    app.config.from_envvar('DONTHACKME_API_SETTINGS')
    print app.config.get("MONGODB_SETTINGS")


def create_app(app_name=None, blueprints=None):
    """Create the flask app."""
    if app_name is None:
        app_name = "cowrie_api"
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    app = Flask(app_name)

    configure_app(app)

    db = MongoEngine()
    db.app = app
    db.init_app(app)

    configure_blueprints(app, blueprints)

    return app


if __name__ == "__main__":
    app = create_app(app_name=__name__)
    app.run(host="0.0.0.0", port=5000, debug=True)
