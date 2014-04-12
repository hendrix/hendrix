import importlib
import os
import sys
import time

import cPickle as pickle

from os import environ
from sys import executable
from socket import AF_INET

from hendrix import HENDRIX_DIR, import_wsgi
from hendrix.contrib.services.cache import CacheService
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

    def __init__(self):


        self.options = HendrixDeploy.setOptions()

        wsgi = self.options['wsgi']
        settings = self.options['settings']

        wsgi_module = import_wsgi(wsgi)
        settings_module = importlib.import_module(settings)
        os.environ['DJANGO_SETTINGS_MODULE'] = settings

        self.application = wsgi_module.application

        self.is_secure = self.options['key'] and self.options['cert']

        self.services = get_additional_services(settings_module)
        self.resources = get_additional_resources(settings_module)

        self.servers = []

    @classmethod
    def setOptions(cls):
        parser = HendrixParser().all_args()
        return vars(parser.parse_args(sys.argv[1::]))

    def addServices(self):
        self.addHendrix()

        if self.is_secure:
            self.addSSLService()

        if self.options.get('local_cache'):
            self.addLocalCacheService()

        self.catalogServers(self.hendrix)



    def addHendrix(self):
        self.hendrix = HendrixService(
            self.application, self.options['http_port'], resources=self.resources,
            services=self.services
        )


    def catalogServers(self, hendrix):
        for service in hendrix.services:
            if isinstance(service, TCPServer) or isinstance(service, SSLServer):
                self.servers.append(service.name)


    def addLocalCacheService(self):
        cache_port = self.options.get('cache_port')
        http_port = self.options.get('http_port')
        _cache = CacheService(host='localhost', from_port=cache_port, to_port=http_port, path='')
        _cache.setName('cache')
        _cache.setServiceParent(self.hendrix)
        self.servers.append('cache')


    def addSSLService(self):

        ssl_port = self.options['ssl_port']
        key = self.options['key']
        cert = self.options['cert']

        _tcp = self.hendrix.getServiceNamed('main_web_tcp')
        factory = _tcp.factory

        _ssl = ssl.SSLServer(ssl_port, factory, key, cert)

        _ssl.setName('main_web_ssl')
        _ssl.setServiceParent(self.hendrix)

        self.servers.append('main_web_ssl')



    def run(self):
        self.addServices()
        action = self.options['action']
        fd = self.options['fd']
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
            HENDRIX_DIR, self.options['http_port'], self.options['settings'].replace('.', '_')
        )

    def getSpawnArgs(self):
        """
        For the child processes we don't need to specify the SSL or caching
        parameters as 
        """
        _args = [
            executable,  # path to python executable e.g. /usr/bin/python
            __file__,  # path to this module
            'start',
            self.options['settings'],
            self.options['wsgi'],
            '--http_port', str(self.options['http_port']),
            '--ssl_port', str(self.options['ssl_port']),
            '--workers', '0',
            '--fd', pickle.dumps(self.fds)
        ]

        return _args


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
                self.fds = {}
                for name in self.servers:
                    port = self.hendrix.get_port(name)
                    fd = port.fileno()
                    childFDs[fd] = fd
                    self.fds[name] = fd

                args = self.getSpawnArgs()
                transports = []
                for i in range(self.options['workers']):
                    transport = reactor.spawnProcess(
                        None, executable, args, childFDs=childFDs, env=environ
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
                if name == 'main_web_ssl':
                    privateCert = PrivateCertificate.loadPEM(
                        open(self.options['cert']).read() + open(self.options['key']).read()
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
    deploy = HendrixDeploy()
    deploy.run()
