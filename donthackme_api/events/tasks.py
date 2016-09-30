"""Celery Tasks for event insertion."""
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

import json
import netaddr
import socket
import sys

from datetime import datetime

from donthackme_elasticsearch.models import IpLocation

from donthackme_elasticsearch import asciinema
from donthackme_api.extensions import (es, celery)

reload(sys)
sys.setdefaultencoding('utf8')


def _geoip(ip_address):
    """Geolocate IP."""
    ip_address = int(netaddr.IPAddress(ip_address))
    location = IpLocation.objects(
        ip_from__lte=ip_address,
        ip_to__gt=ip_address
    ).first()

    return location


def _ensure_ip(address):
    try:
        socket.inet_aton(address)
        return address
    except:
        return socket.gethostbyname(address)


@celery.task
def process_object(index, collection_name, obj, upload_asciinema=True):
    """Process a MongoEngine object."""
    item = obj.to_dict()
    item["doc_id"] = str(obj.id)
    if collection_name == "sensor":
        location = _geoip(item["ip"])
        item["country"] = location.country_name
        item["region"] = location.region_name
        item["city"] = location.city_name
        item["location"] = {
            "lat": location.lat,
            "lon": location.lon
        }
    if collection_name == "session":
        item["timestamp"] = item["start_time"]
        location = _geoip(item["source_ip"])
        item["src_country"] = location.country_name
        item["src_region"] = location.region_name
        item["src_city"] = location.city_name
        item["src_location"] = {
            "lat": location.lat,
            "lon": location.lon
        }
        if "ttylog" in item and \
                "end_time" in item and \
                item["ttylog"]["size"] > 300:
            process_ttylog.delay(
                collection_name,
                obj,
                item,
                upload_asciinema=upload_asciinema
            )
    print("{0}:  {1}  -  {2}".format(
        str(datetime.utcnow()),
        collection_name,
        item["doc_id"]
    ))
    for key in ["source_ip", "dest_ip"]:
        if key in item:
            item[key] = _ensure_ip(item[key])
    es.index(
        index=index,
        doc_type=collection_name,
        id=item["doc_id"],
        body=item
    )


@celery.task
def process_ttylog(index, collection_name, obj,
                   item, upload_asciinema=True):
    """Process the upload of ttylog."""
    outfp, thelog = asciinema.convert_log(obj)
    item["ttylog"]["asciicast"] = json.dumps(thelog, indent=4)
    log_url = None

    print("{0}:  {1}  -  {2} - asciinema_url: {3}".format(
        str(datetime.utcnow()),
        collection_name,
        item["doc_id"],
        log_url
    ))

    es.index(
        index=index,
        doc_type=collection_name,
        id=item["doc_id"],
        body=item
    )
