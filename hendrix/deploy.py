import importlib
import os
import sys
import time

import cPickle as pickle

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
        self.options = {
            'action': action,
            'settings': settings,
            'wsgi': wsgi,
            'port': port,
            'workers': workers,
        }

        wsgi_module = import_wsgi(wsgi)
        settings_module = importlib.import_module(settings)
        os.environ['DJANGO_SETTINGS_MODULE'] = settings

        self.services = get_additional_services(settings_module)
        self.resources = get_additional_resources(settings_module)

        self.hendrix = HendrixService(
            wsgi_module.application, port, resources=self.resources,
            services=self.services
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
            HENDRIX_DIR, self.options['port'], self.options['settings'].replace('.', '_')
        )

    def start(self, fd=None):
        pids = [str(os.getpid())]  # script pid
        servers = ['web_tcp',]
        servers += [
            name for name, service in self.services
            if isinstance(service, TCPServer) or isinstance(service, SSLServer)
        ]
        if fd is None:
            # anything in this block is only run once

            # TODO add global services here, possibly add a services kwarg on
            # __init__

            self.hendrix.startService()
            if self.options['workers']:
                # Create a new listening port and several other processes to help out.
                childFDs = {0: 0, 1: 1, 2: 2}
                fds = {}
                for name in servers:
                    port = self.hendrix.get_port(name)
                    fd = port.fileno()
                    childFDs[fd] = fd
                    fds[name] = fd

                child_args = [
                    executable,  # path to python executable e.g. /usr/bin/python
                    __file__,  # path to this module
                    'start',
                    self.options['settings'],
                    self.options['wsgi'],
                    str(self.options['port']),
                    '0',
                    pickle.dumps(fds)
                ]
                for i in range(self.options['workers']):
                    transport = reactor.spawnProcess(
                        None, executable, child_args,
                        childFDs=childFDs,
                        env=environ
                    )
                    pids.append(str(transport.pid))
            with open(self.pid, 'w') as pid_file:
                pid_file.write('\n'.join(pids))
        else:
            # Another process created the port, drop the tcp service and
            # just start listening on it.
            fds = pickle.loads(fd)
            factories = {}
            for name in servers:
                factory = self.disownService(name)
                factories[name] = factory
            self.hendrix.startService()

            for name, factory in factories.iteritems():
                port = reactor.adoptStreamPort(fds[name], AF_INET, factory)

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

    def disownService(self, name):
        _service = self.hendrix.getServiceNamed(name)
        _service.disownServiceParent()
        return _service.factory


if __name__ == '__main__':
    parser = HendrixParser().all_args()
    arguments = vars(parser.parse_args())
    HendrixDeploy(**arguments)
