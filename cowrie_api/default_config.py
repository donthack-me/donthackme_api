"""Default Configuration Options for the Cowrie Mongo API."""

# Server Settings
API_VERSION = "v1"
HOST = "0.0.0.0"
PORT = 5000

# Mongo
MONGODB_SETTINGS = {
    'db': 'test',
}

# Application Settings
PASSWORD_LENGTH = 24

# Flask Settings
JSONIFY_PRETTYPRINT_REGULAR = True
