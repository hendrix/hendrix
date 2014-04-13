import argparse
from hendrix import defaults

class HendrixParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(HendrixParser, self).__init__(*args, **kwargs)
        if not self.description:
            self.description="The Hendrix Development Server"

    def base_args(self):
        self.add_argument('settings', help='Location of the settings object e.g. myproject.app.settings')
        self.add_argument('wsgi', help='Location of the wsgi object e.g. ./wsgi.py')
        return self

    def all_args(self):
        self.add_argument('--http_port', type=int, default=defaults.HTTP_PORT, help='Enter a port number for the server to serve content.')
        self.add_argument('--https_port', type=int, default=defaults.HTTPS_PORT, help='Enter an ssl port number for the server to serve secure content.')
        self.add_argument('--cache_port', type=int, default=defaults.CACHE_PORT, help='Enter an cache port number to serve cached content.')
        self.add_argument('--local_cache', action='store_true', help='Choice of process local cache or process shared cache')
        self.add_argument('--nocache', action='store_true', help='Disable cache')
        self.add_argument('--workers', type=int, default=0, help='Number of processes to run')
        self.add_argument('--key', type=str, default=None, help='Absolute path to SSL private key')
        self.add_argument('--cert', type=str, nargs='?', default=None, help='Absolute path to SSL public certificate')
        self.add_argument('--fd', type=str, nargs='?', default=None, help='DO NOT SET THIS')
        self.add_argument('action', help='Use start, stop, or restart')
        self.base_args()

        return self
