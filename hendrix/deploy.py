import importlib
import os
import sys
import time

from os import environ
from sys import executable
from socket import AF_INET

from hendrix import HENDRIX_DIR, import_wsgi
from hendrix.parser import HendrixParser
from hendrix.resources import get_additional_resources
from hendrix.services import get_additional_services, HendrixService
from twisted.internet import reactor



class HendrixDeploy(object):

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
        return '%s/%s_%s.pid' % (
            HENDRIX_DIR, self.port, self.settings.replace('.', '_')
        )

    def start(self, fd=None):
        pids = [str(os.getpid())]  # script pid
        if fd is None:
            self.service.startService()
            if self.workers:
                # Create a new listening port and several other processes to help out.
                port = self.service.tcp_port
                # import ipdb; ipdb.set_trace()
                for i in range(self.workers):
                    transport = reactor.spawnProcess(
                            None, executable, [executable, __file__, 'start', self.settings, self.wsgi, str(self.port), '0', str(port.fileno())],
                        childFDs={0: 0, 1: 1, 2: 2, port.fileno(): port.fileno()},
                        env=environ)
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
        time.sleep(1)
        self.start(fd)


if __name__ == '__main__':
    parser = HendrixParser().all_args()
    arguments = vars(parser.parse_args())
    HendrixDeploy(**arguments)
