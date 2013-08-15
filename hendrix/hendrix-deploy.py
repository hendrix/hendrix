import logging.config
import subprocess
import sys, os, errno
import logging
from path import path
from hendrix.path_settings import LOG_DIRECTORY, VIRTUALENV
logger = logging.getLogger(__name__)

deployment_directory = path(__file__).abspath().dirname()

def exit_show_usage():
    exit('Usage: deploy.py <start / stop / restart> <DEPLOYMENT_TYPE> <wsgi.py> <PORT>')

try:
    ACTION = sys.argv[1]
    if ACTION not in ['start', 'stop', 'restart']:
        exit_show_usage()
        
    DEPLOYMENT_TYPE = sys.argv[2]
    WSGI = sys.argv[3]
except IndexError:
        exit_show_usage()

if ACTION != "stop":
    try:
        PORT = sys.argv[4]
    except IndexError:
        exit('Usage: deploy.py (re)start <port>)')

# For now, PID files will live in ./pids.  Later, we'll develop a smarter place.
PID_DIRECTORY = '%s/pids' % deployment_directory

# Let's make sure that the directory exists.
try:
    os.makedirs(PID_DIRECTORY)
except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(PID_DIRECTORY):
        pass
    else: raise


PID_FILE = '%s/%s.pid' % (PID_DIRECTORY, DEPLOYMENT_TYPE)


def start():
    subprocess.call(['%s/bin/twistd' % VIRTUALENV,
                     '--pidfile',
                     PID_FILE,
                     'hendrix',
                     '--port',
                     PORT,
                     '--deployment_type',
                     DEPLOYMENT_TYPE,
                     '--wsgi',
                     WSGI,
                     ])


def stop():
    try:
        pid_file = open(PID_FILE)
        pid = pid_file.read()
        result = subprocess.call(['kill', pid])
        if result:
            print "\nThere is no server currently running with process ID %s." % pid
        else:
            print "Stopped process %s" % pid
    except IOError:
        print "No pid file called %s " % PID_FILE

if ACTION == "start":
    start()

if ACTION == "stop":
    stop()

if ACTION == "restart":
    stop()
    start()
