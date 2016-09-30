DontHack.Me API
==========

This project serves as an authenticated API backend for the [Cowrie Honepot][1]. This API will be used to promote unidirectional data flow, for distributed collection of attack vector information.


Configuration
-------------

Default Configuration can be seen in cowrie_api/default_config.py. You'll likely want to change your mongodb cluster information. These settings follow the standard [Flask-MongoEngine][2] Configuration options. To establish an SSL-authenticated connection to [ObjectRocket][3], for example, you would want to create your own config.py that looks like this:

```python
"""Local Configuration for Cowrie-API."""
MONGODB_SETTINGS = {
    "host": "{{your connection info}}.objectrocket.com",
    "port": 26008,
    "db": "yourdbname",
    "username": "yourusername",
    "password": "your password",
    "ssl": True
SECRET_KEY = "A LONG SALT FOR USE IN PASSWORD HASHING"
}
```

Running The Server
------------------

To run the server, set the path to your config file, and then simply run the executable:

```bash
~/donthackme_api [ export DONTHACKME_API_SETTINGS=donthackme_api/config.py
~/donthackme [ python app.py
```

TODO
----
* Establish True Authentication (Leverage Keystone possibly?).
* Write Tests.

[1]: https://github.com/micheloosterhof/cowrie
[2]: http://docs.mongoengine.org/projects/flask-mongoengine/en/latest/
[3]: http://objectrocket.com/
