import importlib
import os
import sys
import time

import cPickle as pickle

from os import environ
from sys import executable
from socket import AF_INET

from django.conf import settings

from hendrix import HENDRIX_DIR, import_wsgi, defaults
from hendrix.contrib.services.cache import CacheService
from hendrix.contrib import ssl, DevWSGIHandler
from hendrix.contrib.color import Colors
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
    """

    def __init__(self, action='start', options=None):
        self.action = action
        self.options = options
        self.options = HendrixDeploy.getConf(self.options)
        # get wsgi
        if not self.options['dev']:
            wsgi_dot_path = getattr(settings, 'WSGI_APPLICATION', None)
            wsgi_module, application_name = wsgi_dot_path.split('.')
            wsgi = importlib.import_module(wsgi_module)
            self.application = getattr(wsgi, application_name, None)
        else:
            self.application = DevWSGIHandler()
            Colors.blue('Ready and Listening...')

        self.is_secure = self.options['key'] and self.options['cert']

        self.services = get_additional_services(settings)
        self.resources = get_additional_resources(settings)

        self.servers = []

    @classmethod
    def getConf(cls, options):
        "updates the options dict to use config options in the settings module"
        ports = ['http_port', 'https_port', 'cache_port']
        for port_name in ports:
            port = getattr(settings, port_name.upper(), None)
            # only use the settings ports if the defaults were left unchanged
            default = getattr(defaults, port_name.upper())
            if port and options.get(port_name) == default:
                options[port_name] = port

        _opts = [('key', 'hx_private_key'), ('cert', 'hx_certficate'), ('wsgi', 'wsgi_application')]
        for opt_name, settings_name in _opts:
            opt = getattr(settings, settings_name.upper(), None)
            if opt:
                options[opt_name] = opt

        if not options['settings']:
            options['settings'] = environ['DJANGO_SETTINGS_MODULE']
        return options


    def addServices(self):
        """
        a helper function used in HendrixDeploy.run
        it instanstiates the HendrixService and adds child services
        note that these services will also be run on all processes
        """
        self.addHendrix()

        if not self.options.get('global_cache') and not self.options.get('nocache'):
            self.addLocalCacheService()

        if self.is_secure:
            self.addSSLService()

        self.catalogServers(self.hendrix)



    def addHendrix(self):
        "instantiates the HendrixService"
        self.hendrix = HendrixService(
            self.application, self.options['http_port'], resources=self.resources,
            services=self.services
        )


    def catalogServers(self, hendrix):
        "collects a list of service names serving on TCP or SSL"
        for service in hendrix.services:
            if isinstance(service, TCPServer) or isinstance(service, SSLServer):
                self.servers.append(service.name)


    def getCacheService(self):
        cache_port = self.options.get('cache_port')
        http_port = self.options.get('http_port')
        return CacheService(
            host='localhost', from_port=cache_port, to_port=http_port, path=''
        )

    def addLocalCacheService(self):
        "adds a CacheService to the instatiated HendrixService"
        _cache = self.getCacheService()
        _cache.setName('cache_proxy')
        _cache.setServiceParent(self.hendrix)


    def addSSLService(self):
        "adds a SSLService to the instaitated HendrixService"
        https_port = self.options['https_port']
        key = self.options['key']
        cert = self.options['cert']

        _tcp = self.hendrix.getServiceNamed('main_web_tcp')
        factory = _tcp.factory

        _ssl = ssl.SSLServer(https_port, factory, key, cert)

        _ssl.setName('main_web_ssl')
        _ssl.setServiceParent(self.hendrix)


    def run(self):
        "sets up the desired services and runs the requested action"
        self.addServices()
        action = self.action
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
        ]
        if not self.options['loud']:
            _args += ['-W', 'ignore',]
        _args += [
            'manage.py',
            'hx',
            'start',
            '--http_port', str(self.options['http_port']),
            '--https_port', str(self.options['https_port']),
            '--cache_port', str(self.options['cache_port']),
            '--workers', '0',
            '--fd', pickle.dumps(self.fds),
        ]
        if self.is_secure:
            _args += [
                '--key', self.options.get('key'),
                '--cert', self.options.get('cert')
            ]
        if self.options['traceback']:
            _args.append('--traceback')
        return _args


    def addGlobalServices(self):
        if self.options.get('global_cache') and not self.options.get('nocache'):
            _cache = self.getCacheService()
            _cache.startService()


    def start(self, fd=None):
        pids = [str(os.getpid())]  # script pid

        if fd is None:
            # anything in this block is only run once

            # TODO add global services here, possibly add a services kwarg on
            # __init__
            self.addGlobalServices()

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
        """
        disowns a service on hendirix by name
        returns a factory for use in the adoptStreamPort part of setting up
        multiple processes
        """
        _service = self.hendrix.getServiceNamed(name)
        _service.disownServiceParent()
        return _service.factory
