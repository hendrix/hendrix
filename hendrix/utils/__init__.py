import os, sys
from path import path


HENDRIX_DIR = path(__file__).abspath().dirname()

SHARE_PATH = os.path.join(
    os.path.dirname(sys.executable),
    'share/hendrix'
)

def get_pid(options):
    """returns The default location of the pid file for process management"""
    namespace = options['settings'] if options['settings'] else options['wsgi']
    return '%s/%s_%s.pid' % (
        HENDRIX_DIR, options['http_port'], namespace.replace('.', '_')
    )
