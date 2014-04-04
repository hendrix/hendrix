import importlib
import os
import sys
import time

from os import environ
from sys import executable
from socket import AF_INET

from hendrix import HENDRIX_DIR, import_wsgi
from hendrix.contrib.cache import CacheServer
from hendrix.parser import HendrixParser
from hendrix.resources import get_additional_resources
from hendrix.services import get_additional_services, HendrixService
from twisted.internet import reactor



class HendrixDeploy(object):
    """
    HendrixDeploy encapsulates the necessary information needed to deploy the
    HendrixService on a single or multiple processes.
        action: [start|stop|restart]
        settings: dot seperated python path to django settings module e.g. proj.settings
        wsgi: the relative or absolute path to a wsgi.py file. It's important
            to note that this file is also used to expose the projects path to
            python.
        port: the listening port
        workers: the number of process you want to start minus 1 i.e. 2 yeilds 3 processes
        fd: file descriptor that is needed to expose the listening port to sub-
            processes of the reactor
    """
    def __init__(self, action, settings, wsgi, port, workers=2, fd=None):
        self.action = action
        self.settings = settings
        self.wsgi = wsgi
        self.port = port
        self.workers = workers
        wsgi_module = import_wsgi(wsgi)
        settings_module = importlib.import_module(settings)
        os.environ['DJANGO_SETTINGS_MODULE'] = settings

        self.service = HendrixService(
            wsgi_module.application, port,
            resources=get_additional_resources(settings_module),
            services=get_additional_services(settings_module)
        )
        if action == 'start':
            getattr(self, action)(fd)
        elif action == 'restart':
            getattr(self, action)(sig=9, fd=fd)
        else:
            getattr(self, action)()

    @property
    def pid(self):
        "The default location of the pid file for process management"
        return '%s/%s_%s.pid' % (
            HENDRIX_DIR, self.port, self.settings.replace('.', '_')
        )

    def start(self, fd=None):
        pids = [str(os.getpid())]  # script pid
        if fd is None:
            # anything in this block is only run once

            # TODO add global services here, possibly add a services kwarg on
            # __init__

            self.service.startService()
            if self.workers:
                # Create a new listening port and several other processes to help out.
                port = self.service.tcp_port
                fileno = port.fileno()
                child_args = [
                    executable,  # path to python executable e.g. /usr/bin/python
                    __file__,  # path to this module
                    'start',
                    self.settings,
                    self.wsgi,
                    str(self.port),
                    '0',
                    str(fileno)
                ]
                for i in range(self.workers):
                    transport = reactor.spawnProcess(
                        None, executable, child_args,
                        childFDs={0: 0, 1: 1, 2: 2, fileno: fileno},
                        env=environ
                    )
                    pids.append(str(transport.pid))
            with open(self.pid, 'w') as pid_file:
                pid_file.write('\n'.join(pids))
        else:
            # Another process created the port, drop the tcp service and
            # just start listening on it.
            self.service.tcp_service.disownServiceParent()
            self.service.startService()
            port = reactor.adoptStreamPort(fd, AF_INET, self.service.factory)

        reactor.run()

    def stop(self, sig=9):
        with open(self.pid) as pid_file:
            pids = pid_file.readlines()
            for pid in pids:
                try:
                    os.kill(int(pid), sig)
                except OSError:
                    # OSError is raised when it trys to kill the child processes
                    pass
        os.remove(self.pid)

    def restart(self, sig=9, fd=None):
        self.stop(sig)
        time.sleep(1)  # wait a second to ensure the port is closed
        self.start(fd)


if __name__ == '__main__':
    parser = HendrixParser().all_args()
    arguments = vars(parser.parse_args())
    HendrixDeploy(**arguments)
