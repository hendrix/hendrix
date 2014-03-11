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
class HendrixAction(object):

    def __init__(self, action=None, port=None, settings=None, wsgi=None):
        self.action = action
        self.settings = settings
        self.wsgi = wsgi
        self.port = port
        actions = ['start', 'stop', 'restart']
        if self.action not in actions:
            # import ipdb; ipdb.set_trace()
            help_txt = build_parser().format_help()
            msg = (
                '%s not in %s. See below for help:\n\n%s'
            ) % (self.action, actions, help_txt)
            # exit(msg)
            raise RuntimeError(msg)


    def execute(self):
        if self.action == 'start':
            self.start()

        if self.action == 'stop':
            self.stop()

        if self.action == 'restart':
            self.restart()


    def start(self):
        """
        Method to start a twisted daemon using the hendrix plugin.
        """
        if not is_port_free(self.port):
            specs_dict = dict(list_taken_specs())
            settings = specs_dict[self.port]
            exit(
                '\n\
Port %(port_number)s is already in use. Please choose a different port.\n\
Alternatively you could restart the process by excuting:\n\
    hendix-deploy.py restart %(dt)s ./wsgi %(port_number)s\n' % {
                'port_number': self.port,
                'dt': settings
            }
        )

        _PID_FILE = pid_ref(self.port, self.settings)

        # Parts of the command list to pass to subprocess.call
        twisted_part = ['%s/bin/twistd' % VIRTUALENV, '--pidfile', _PID_FILE]
        hendrix_part = ['hendrix', '--port', str(self.port), '--settings', self.settings, '--wsgi', self.wsgi]
        cmd = twisted_part + hendrix_part

        # Execute the command
        subprocess.check_call(cmd)
        print "Hendrix server started..."


    # All any function should need is the port and the deployment type to kill an
    # existing twisted process
    def stop(self):
        """
        Method used to kill a given twisted process.
        """
        _PID_FILE = pid_ref(self.port, self.settings)
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


    def restart(self):
        """
        Method used to restart a given twisted process
        """
        try:
            self.stop()
            self.start()
        except (IOError, subprocess.CalledProcessError) as e:
            print e

###############################################################################
#
# Helper functions
#
###############################################################################
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
    parser.add_argument('ACTION', help='Use start, stop, or restart')
    parser.add_argument('SETTINGS', help='The location of the settings object')
    parser.add_argument('WSGI', help='The location of the wsgi object')
    parser.add_argument('PORT',
    help='Enter a port number for serving content', type=int)

    return parser


def process(arguments):
    ACTION = arguments['ACTION']
    SETTINGS = arguments['SETTINGS']
    WSGI = arguments['WSGI']
    PORT = arguments['PORT']

    # Let's make sure that the directory exists.
    try:
        os.makedirs(_PID_DIRECTORY)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(_PID_DIRECTORY):
            pass
        else:
            raise

    return HendrixAction(ACTION, PORT, SETTINGS, WSGI)



###############################################################################
#
# Let the scripting fun begin...
#
###############################################################################
if __name__ == "__main__":
    arguments = vars(build_parser().parse_args())
    hendrix_action = process(arguments)
    hendrix_action.execute()
