from hendrix import HENDRIX_DIR
import os, sys

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
