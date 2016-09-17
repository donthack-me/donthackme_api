"""Admin Blueprint for donthack.me."""
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

from flask import Blueprint

from donthackme_api.models import Sensor

admin = Blueprint('admin', __name__, url_prefix="/admin")


@admin.route("/health", methods=["GET"])
def test_health():
    try:
        Sensor.objects()
    except:
        return "Couldn't connect to DB!", 500
    else:
        return "All Good!", 200
