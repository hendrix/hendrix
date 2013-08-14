import logging.config
import subprocess
import sys, os, errno
import logging
from path import path
from path_settings import set_path, LOG_DIRECTORY, VIRTUALENV
set_path()  # So that private is on path.
logger = logging.getLogger(__name__)

deployment_directory = path(__file__).abspath().dirname()

def exit_show_usage():
    exit('Usage: deploy.py <start / stop / restart> <DEPLOYMENT_TYPE> <PORT> ')

try:
    ACTION = sys.argv[1]
    if ACTION not in ['start', 'stop', 'restart']:
        exit_show_usage()
        
    DEPLOYMENT_TYPE = sys.argv[2]
except IndexError:
        exit_show_usage()

if ACTION == "start":
    try:
        PORT = sys.argv[3]
    except IndexError:
        exit('Usage: deploy.py start <port>)')

# For now, PID files will live in ./pids.  Later, we'll develop a smarter place.
PID_DIRECTORY = '%s/pids' % deployment_directory

# Let's make sure that the directory exists.
try:
    os.makedirs(PID_DIRECTORY)
except OSError as exc: # Python >2.5
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
                     '--DEPLOYMENT_TYPE',
                     DEPLOYMENT_TYPE
                     ])


def stop():
    try:
        pid_file = open(PID_FILE)
        pid = pid_file.read()
        result = subprocess.call(['kill', pid])
        if result:
            print "\nThere is no server currently running with process ID %s." % pid
        else:
            exit(0)
    except IOError:
        print "No pid file called %s " % PID_FILE
    print "\nDid you mean to 'start' the server?\n  Let's try that."
    start()

if ACTION == "start":
    start()
    logger.debug('twisted started!')

if ACTION == "stop":
    stop()
    logger.debug('twisted stoped!')

if ACTION == "restart":
    stop()
    start()
    logger.debug('twisted restarted!')
