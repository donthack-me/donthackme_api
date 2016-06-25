"""Cowrie Frontend API WSGI File."""
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

from cowrie_api import app

# Add the app's directory to the PYTHONPATH
BASE_DIR = os.path.join(os.path.dirname(__file__))

# Activate your virtual env
activate_env = os.path.join(BASE_DIR, "venv/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Give WSGI the "application"
appplication = app.create_app()