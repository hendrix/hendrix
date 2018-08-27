import os

CACHE_PORT = 8080
HTTP_PORT = 8000
HTTPS_PORT = 4430

DEFAULT_MAX_AGE = 3600

DEFAULT_LOG_PATH = os.path.dirname(__file__)
DEFAULT_LOG_FILE = os.path.join(DEFAULT_LOG_PATH, 'default-hendrix.log')
