from hendrix import HENDRIX_DIR


def get_pid(options):
    """returns The default location of the pid file for process management"""
    return '%s/%s_%s.pid' % (
        HENDRIX_DIR, options['http_port'], options[
            'settings'].replace('.', '_')
    )