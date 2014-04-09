import importlib
import os
import sys
import time

import cPickle as pickle

from os import environ
from sys import executable
from socket import AF_INET

from hendrix import HENDRIX_DIR, import_wsgi
from hendrix.contrib.cache import CacheService
from hendrix.contrib import ssl
from hendrix.parser import HendrixParser
from hendrix.resources import get_additional_resources
from hendrix.services import get_additional_services, HendrixService
from twisted.application.internet import TCPServer, SSLServer
from twisted.internet import reactor, protocol
from twisted.internet.ssl import PrivateCertificate
from twisted.protocols.tls import TLSMemoryBIOFactory



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
    def __init__(self, action, settings, wsgi, port, workers=2, privkey=None, cert=None, fd=None):
        default_proxy_port = 8765
        self.options = {
            'action': action,
            'settings': settings,
            'wsgi': wsgi,
            'port': port,
            'workers': workers,
            'privkey': privkey,
            'cert': cert
        }
        wsgi_module = import_wsgi(wsgi)
        settings_module = importlib.import_module(settings)
        os.environ['DJANGO_SETTINGS_MODULE'] = settings

        self.services = get_additional_services(settings_module)
        self.resources = get_additional_resources(settings_module)

        self.servers = ['web_tcp',]
        default_cache = True
        for name, service in self.services:
            if isinstance(service, TCPServer) or isinstance(service, SSLServer):
                self.servers.append(name)
            default_cache &= not isinstance(service, CacheService)

        if default_cache:
            self.servers.append('cache')
            self.services.append(
                ('cache', CacheService(site_port=default_proxy_port, proxy_port=port))
            )
            port = default_proxy_port
            self.options['port'] = port

        self.hendrix = HendrixService(
            wsgi_module.application, port, resources=self.resources,
            services=self.services
        )

        self.is_secure = False
        if self.options['privkey'] and self.options['cert']:
            web_tcp = self.hendrix.getServiceNamed('web_tcp')
            factory = web_tcp.factory
            web_ssl = ssl.SSLServer(443, factory, privkey, cert)
            web_ssl.setName('web_ssl')
            web_ssl.setServiceParent(self.hendrix)
            self.servers.append('web_ssl')
            self.is_secure = True

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

        if fd is None:
            # anything in this block is only run once

            # TODO add global services here, possibly add a services kwarg on
            # __init__

            self.hendrix.startService()
            if self.options['workers']:
                # Create a new listening port and several other processes to help out.
                childFDs = {0: 0, 1: 1, 2: 2}
                fds = {}
                for name in self.servers:
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
                ]
                if self.is_secure:
                    child_args.append(self.options['privkey'])
                    child_args.append(self.options['cert'])
                child_args.append(pickle.dumps(fds))
                transports = []
                for i in range(self.options['workers']):
                    transport = reactor.spawnProcess(
                        None, executable, child_args,
                        childFDs=childFDs,
                        env=environ
                    )
                    transports.append(transport)
                    pids.append(str(transport.pid))
            with open(self.pid, 'w') as pid_file:
                pid_file.write('\n'.join(pids))
        else:
            # Another process created the port, drop the tcp service and
            # just start listening on it.
            fds = pickle.loads(fd)
            factories = {}
            for name in self.servers:
                factory = self.disownService(name)
                factories[name] = factory
            self.hendrix.startService()
            for name, factory in factories.iteritems():
                if name == 'web_ssl':
                    privateCert = PrivateCertificate.loadPEM(
                        open(self.options['cert']).read() + open(self.options['privkey']).read()
                    )
                    factory = TLSMemoryBIOFactory(
                        privateCert.options(), False, factory
                    )
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
