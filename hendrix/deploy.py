import chalk
import importlib
import os
import time

import cPickle as pickle

from os import environ
from sys import executable
from socket import AF_INET

from hendrix import defaults
from hendrix.contrib import ssl
from hendrix.contrib.services.cache import CacheService
from hendrix.options import options as hx_options
from hendrix.resources import get_additional_resources
from hendrix.services import get_additional_services, HendrixService
from hendrix.utils import get_pid
from twisted.application.internet import TCPServer, SSLServer
from twisted.internet import reactor
from twisted.internet.ssl import PrivateCertificate
from twisted.protocols.tls import TLSMemoryBIOFactory


class HendrixDeploy(object):
    """
    HendrixDeploy encapsulates the necessary information needed to deploy the
    HendrixService on a single or multiple processes.
    """

    def __init__(self, action='start', options={}, reactor=reactor):
        self.action = action
        self.options = hx_options()
        self.options.update(options)
        self.services = []
        self.resources = []
        self.reactor = reactor

        self.use_settings = True
        # because running the management command overrides self.options['wsgi']
        if self.options['wsgi']:
            wsgi_dot_path = self.options['wsgi']
            self.application = HendrixDeploy.importWSGI(wsgi_dot_path)
            self.use_settings = False
        else:
            os.environ['DJANGO_SETTINGS_MODULE'] = self.options['settings']
            django_conf = importlib.import_module('django.conf')
            settings = getattr(django_conf, 'settings')
            self.services = get_additional_services(settings)
            self.resources = get_additional_resources(settings)
            self.options = HendrixDeploy.getConf(settings, self.options)

        if self.use_settings:
            wsgi_dot_path = getattr(settings, 'WSGI_APPLICATION', None)
            self.application = HendrixDeploy.importWSGI(wsgi_dot_path)

        self.is_secure = self.options['key'] and self.options['cert']

        self.servers = []

    @classmethod
    def importWSGI(cls, wsgi_dot_path):
        wsgi_module, application_name = wsgi_dot_path.rsplit('.', 1)
        wsgi = importlib.import_module(wsgi_module)
        return getattr(wsgi, application_name, None)

    @classmethod
    def getConf(cls, settings, options):
        "updates the options dict to use config options in the settings module"
        ports = ['http_port', 'https_port', 'cache_port']
        for port_name in ports:
            port = getattr(settings, port_name.upper(), None)
            # only use the settings ports if the defaults were left unchanged
            default = getattr(defaults, port_name.upper())
            if port and options.get(port_name) == default:
                options[port_name] = port

        _opts = [
            ('key', 'hx_private_key'),
            ('cert', 'hx_certficate'),
            ('wsgi', 'wsgi_application')
        ]
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
            self.application, self.options['http_port'],
            resources=self.resources, services=self.services,
            loud=self.options['loud']
        )

    def catalogServers(self, hendrix):
        "collects a list of service names serving on TCP or SSL"
        for service in hendrix.services:
            if isinstance(service, (TCPServer, SSLServer)):
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

        if action.startswith('start'):
            chalk.blue('Ready and Listening...')
            getattr(self, action)(fd)
            self.reactor.run()
        elif action == 'restart':
            getattr(self, action)(fd=fd)
        else:
            getattr(self, action)()

    @property
    def pid(self):
        "The default location of the pid file for process management"
        return get_pid(self.options)

    def getSpawnArgs(self):
        """
        For the child processes we don't need to specify the SSL or caching
        parameters as
        """
        _args = [
            executable,  # path to python executable e.g. /usr/bin/python
        ]
        if not self.options['loud']:
            _args += ['-W', 'ignore']
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
        if self.options['nocache']:
            _args.append('--nocache')
        if self.options['dev']:
            _args.append('--dev')
        if self.options['traceback']:
            _args.append('--traceback')
        if self.options['global_cache']:
            _args.append('--global_cache')
        if not self.use_settings:
            _args += ['--wsgi', self.options['wsgi']]
        return _args

    def addGlobalServices(self):
        if self.options.get('global_cache') and not self.options.get('nocache'):
            _cache = self.getCacheService()
            _cache.startService()

    def start(self, fd=None):
        pids = [str(os.getpid())]  # script pid

        if fd is None:
            # anything in this block is only run once
            self.addGlobalServices()

            self.hendrix.startService()
            if self.options['workers']:
                # Create a new listening port and several other processes to
                # help out.
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
                    transport = self.reactor.spawnProcess(
                        None, executable, args, childFDs=childFDs, env=environ
                    )
                    transports.append(transport)
                    pids.append(str(transport.pid))
            with open(self.pid, 'w') as pid_file:
                pid_file.write('\n'.join(pids))
        else:
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
                port = self.reactor.adoptStreamPort(
                    fds[name], AF_INET, factory
                )

    def stop(self, sig=9):
        with open(self.pid) as pid_file:
            pids = pid_file.readlines()
            for pid in pids:
                try:
                    os.kill(int(pid), sig)
                except OSError:
                    # OSError raised when it trys to kill the child processes
                    pass
        os.remove(self.pid)

    def start_reload(self, fd=None):
        self.start(fd=fd)

    def restart(self, fd=None):
        self.stop()
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
