"""
`hendrix-deploy.py` repensents a means of controlling the web service used to
deploy a wsgi application.
"""
import logging
import logging.config
import subprocess
import sys, os, errno
from path import path
from os import listdir
from os.path import isfile, join
from hendrix.path_settings import LOG_DIRECTORY, VIRTUALENV

logger = logging.getLogger(__name__)  # As it stands this file wont do anything since a logging dict isn't specified
hendrix_directory = path(__file__).abspath().dirname()


################################################################################
#
# Defaults
#
################################################################################
# For now, PID files will live in ./pids.  Later, we'll develop a smarter place.
# This will put the pids in folder where hendrix-deploy.py is executed.
_PID_DIRECTORY = '%s/pids' % hendrix_directory
# The following aren't currently in use...
_PORT = 80
_DEPLOYMENT_TYPE = 'test'  # not sure how useful this will be... Needs to be checked for existance
_WSGI = './wsgi.py'

################################################################################
#
# Main functions
#
################################################################################
def start(port, deployment_type, wsgi):
    """
    Method to start a twisted daemon using the hendrix plugin.
    """
    if not is_port_free(port):
        specs_dict = dict(list_taken_specs())
        deployment_type = specs_dict[port]
        exit(
            '\n\
Port %(port)s is already in use. Please choose a different port.\n\
Alternatively you could restart the process by excuting:\n\
    hendix-deploy.py restart %(dt)s ./wsgi %(port)s\n' % {
                'port': port,
                'dt': deployment_type
            }
        )

    _PID_FILE = pid_ref(port, deployment_type)

    # Parts of the command list to pass to subprocess.call
    twisted_part = ['%s/bin/twistd' % VIRTUALENV, '--pidfile', _PID_FILE]
    hendrix_part = ['hendrix', '--port', port, '--deployment_type', deployment_type, '--wsgi', wsgi]
    cmd = twisted_part + hendrix_part
    
    # Execute the command
    subprocess.call(cmd)


# All any function should need is the port and the deployment type to kill an
# existing twisted process
def stop(port, deployment_type):
    """
    Method used to kill a given twisted process.
    """
    _PID_FILE = pid_ref(port, deployment_type)
    try:
        pid_file = open(_PID_FILE)
        pid = pid_file.read()
        result = subprocess.call(['kill', pid])
        if result:
            raise SystemExit("\nThere is no server currently running %s with process ID %s." % (pid_file, pid))
        else:
            print "Stopped process %s" % pid
            # clean up the file
            os.remove(_PID_FILE)
    except IOError: 
        raise IOError("\nNo pid file called %s\n" % _PID_FILE)


def restart(port, deployment_type, wsgi):
    """
    Method used to restart a given twisted process
    """
    try:
        stop(port, deployment_type)
        start(port, deployment_type, wsgi)
    except (IOError, SystemExit) as e:
        print e

################################################################################
#
# Helper functions
#
################################################################################
def exit_show_usage():
    exit('Usage: hendix-deploy.py <start / stop / restart> <DEPLOYMENT_TYPE> <wsgi.py> <PORT>')


def pid_ref(port, deployment_type):
    """
    """
    # Having the port as the first variable in the pid file name makes it easier
    # turn the running services into a dictionary later on.
    return '%s/%s-%s.pid' % (_PID_DIRECTORY, port, deployment_type)


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


################################################################################
#
# Let the scripting fun begin...
#
################################################################################
if __name__ == "__main__":
    try:
        # I understand that this is a very rigid way of handling the script args
        # but it's good enough for now.
        ACTION = sys.argv[1]    
        DEPLOYMENT_TYPE = sys.argv[2]
        WSGI = sys.argv[3]
        PORT = sys.argv[4]

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
        start(PORT, DEPLOYMENT_TYPE, WSGI)

    if ACTION == "stop":
        stop(PORT, DEPLOYMENT_TYPE)

    if ACTION == "restart":
        restart(PORT, DEPLOYMENT_TYPE, WSGI)
