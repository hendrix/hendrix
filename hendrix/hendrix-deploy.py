"""
`hendrix-deploy.py` repensents a means of controlling the web service used to
deploy a wsgi application.
"""
import subprocess
import sys, os, errno
from hendrix import VIRTUALENV, HENDRIX_DIR
from os import listdir
from os.path import isfile, join
import argparse


###############################################################################
#
# Defaults
#
###############################################################################
# For now, PID files will live in ./pids.  Later, we'll develop a smarter place
# This will put the pids in folder where hendrix-deploy.py is executed.
_PID_DIRECTORY = '%s/pids' % HENDRIX_DIR
# The following aren't currently in use...
_PORT = 80
# not sure how useful this will be... Needs to be checked for existance
_SETTINGS = 'test'
_WSGI = './wsgi.py'

###############################################################################
#
# Main functions
#
###############################################################################
def start(port, settings, wsgi):
    """
    Method to start a twisted daemon using the hendrix plugin.
    """
    if not is_port_free(port):
        specs_dict = dict(list_taken_specs())
        settings = specs_dict[port]
        exit(
            '\n\
Port %(port)s is already in use. Please choose a different port.\n\
Alternatively you could restart the process by excuting:\n\
    hendix-deploy.py restart %(dt)s ./wsgi %(port)s\n' % {
                'port': port,
                'dt': settings
            }
        )

    _PID_FILE = pid_ref(port, settings)

    # Parts of the command list to pass to subprocess.call
    twisted_part = ['%s/bin/twistd' % VIRTUALENV, '--pidfile', _PID_FILE]
    hendrix_part = ['hendrix', '--port', port, '--settings', settings, '--wsgi', wsgi]
    cmd = twisted_part + hendrix_part

    # Execute the command
    subprocess.check_call(cmd)
    print "Hendrix server started..."


# All any function should need is the port and the deployment type to kill an
# existing twisted process
def stop(port, settings):
    """
    Method used to kill a given twisted process.
    """
    _PID_FILE = pid_ref(port, settings)
    try:
        pid_file = open(_PID_FILE)
        pid = pid_file.read()
        pid_file.close()
        os.remove(_PID_FILE)  # clean up the file

        subprocess.check_call(['kill', pid])
        print "Stopped process %s" % pid
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError("\nThere is no server currently running %s with process ID %s. Return status [%s]" % (pid_file, pid, e.returncode))
    except IOError:
        raise IOError("\nNo pid file called %s\n" % _PID_FILE)


def restart(port, settings, wsgi):
    """
    Method used to restart a given twisted process
    """
    try:
        stop(port, settings)
        start(port, settings, wsgi)
    except (IOError, subprocess.CalledProcessError) as e:
        print e

###############################################################################
#
# Helper functions
#
###############################################################################
def exit_show_usage():
    exit('Usage: hendix-deploy.py <start / stop / restart> <settings> <wsgi.py> <PORT>')


def pid_ref(port, settings):
    """
    """
    # Having the port as the first variable in the pid file name makes it
    # easier turn the running services into a dictionary later on.
    return '%s/%s-%s.pid' % (_PID_DIRECTORY, port, settings)


def list_files(directory):
    """
    """
    return [item for item in listdir(directory) if isfile(join(directory, item))]


def list_taken_specs():
    """
    """
    pid_files = list_files(_PID_DIRECTORY)
    specs = []

    for proc in pid_files:
        file_name = os.path.splitext(proc)[0]
        spec = file_name.split('-')
        specs.append(spec)

    return specs


def is_port_free(port):
    """
    """
    specs = list_taken_specs()
    ports = [spec[0] for spec in specs]
    if port in ports:
        return False
    return True


def build_parser():
    """
    """
    parser = argparse.ArgumentParser(description='The Hendrix deployment suite')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-start', action='store_false', help='Start the Hendrex server')
    group.add_argument('-stop', action='store_true', help='Stop the Hendrix server')
    group.add_argument('-restart', action='store_false',help='Restart the Hendrix server')
    parser.add_argument('SETTINGS', help='Location of the settings object')
    parser.add_argument('WSGI', help='Location of the wsgi object')
    parser.add_argument('PORT', help='Enter a port number for the server to serve content.')
    return parser

###############################################################################
#
# Let the scripting fun begin...
#
###############################################################################
if __name__ == "__main__":
    parser = build_parser()
    args = vars(parser.parse_args())
    ACTION = args[parser.group]
    SETTINGS = args['SETTINGS']
    WSGI = args['WSGI']
    PORT = args['PORT']

    try:

        if ACTION not in ['start', 'stop', 'restart']:
            exit_show_usage()

    except IndexError:
        exit_show_usage()

    # Let's make sure that the directory exists.
    try:
        os.makedirs(_PID_DIRECTORY)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(_PID_DIRECTORY):
            pass
        else: raise

    if ACTION == "start":
        start(PORT, SETTINGS, WSGI)

    if ACTION == "stop":
        stop(PORT, SETTINGS)

    if ACTION == "restart":
        restart(PORT, SETTINGS, WSGI)
