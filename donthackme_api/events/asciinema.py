"""Asciinema connector to allow direct upload of logs to asciinema."""
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

import io
import json
import struct

import requests
from requests.auth import HTTPBasicAuth


OP_OPEN, OP_CLOSE, OP_WRITE, OP_EXEC = 1, 2, 3, 4
TYPE_INPUT, TYPE_OUTPUT, TYPE_INTERACT = 1, 2, 3


def convert_log(obj):
    """
    Convert the Mongo Session's ttylog.log_binary to json.

    Much of this code is borrowed from the converter included
    with cowrie itself:

    https://github.com/micheloosterhof/cowrie/blob/master/bin/asciinema

    Additionally, due to the multipart/form-data API that asciinema uses,
    There is quite a bit of hackery with the StringIO and BytesIO objects
    to fake files in memory.
    """
    fd = io.BytesIO(obj.ttylog.log_binary)

    title = "Cowrie Recording: {0}_{1}"

    thelog = {}
    thelog['version'] = 1
    thelog['width'] = 80
    thelog['height'] = 24
    thelog['duration'] = 0.0
    thelog['command'] = "/bin/bash"
    thelog['title'] = title.format(obj.session, obj.sensor_name)
    theenv = {}
    theenv['TERM'] = "xterm256-color"
    theenv['SHELL'] = "/bin/bash"
    thelog["env"] = theenv
    stdout = []
    thelog["stdout"] = stdout

    ssize = struct.calcsize('<iLiiLL')

    currtty, prevtime, prefdir = 0, 0, 0
    sleeptime = 0.0

    while 1:
        try:
            (op, tty, length, dir, sec, usec) = \
                struct.unpack('<iLiiLL', fd.read(ssize))
            data = fd.read(length)
        except struct.error:
            break

        if currtty == 0:
            currtty = tty

        if str(tty) == str(currtty) and op == OP_WRITE:
            # the first stream seen is considered 'output'
            if prefdir == 0:
                prefdir = dir
            if dir == prefdir:
                curtime = float(sec) + float(usec) / 1000000
                curtime = curtime / 2
                if prevtime != 0:
                    sleeptime = curtime - prevtime
                prevtime = curtime

                # rtrox: While playback works properly
                #        with the asciinema client, upload
                #        causes mangling of the data due to
                #        newlines being misinterpreted without
                #        carriage returns.
                data = data.replace("\n", "\r\n")

                thedata = [sleeptime, data]
                thelog['duration'] = curtime
                stdout.append(thedata)

        elif str(tty) == str(currtty) and op == OP_CLOSE:
            break

    log_json = json.dumps(thelog, indent=4)
    outfp = io.StringIO(unicode(log_json))
    return outfp, thelog


def upload_file(outfp, username, token):
    """Upload Asciicast to asciinema."""
    resp = requests.post(
        url="https://asciinema.org/api/asciicasts",
        auth=HTTPBasicAuth(username, token),
        files={"asciicast": ("asciicast.json", outfp)}
    )
    if resp.status_code != 201:
        raise ValueError("Upload returned status_code: {0} - {1}".format(
            resp.status_code, resp.text
        ))
    return (resp.text)
