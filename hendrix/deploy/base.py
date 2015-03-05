import chalk
import importlib
import os
import time

import cPickle as pickle

from os import environ
from socket import AF_INET

from hendrix import defaults
from hendrix.options import options as hx_options
from hendrix.resources import get_additional_resources
from hendrix.services import get_additional_services, HendrixService
from hendrix.utils import get_pid
from twisted.application.internet import TCPServer, SSLServer
from twisted.internet import reactor


class HendrixDeploy(object):
    """
    HendrixDeploy encapsulates the necessary information needed to deploy
    the HendrixService on a single or multiple processes.
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
            django = importlib.import_module('django')
            if django.VERSION[:2] >= (1, 7):
                installed_apps = getattr(settings, "INSTALLED_APPS")
                django.apps.apps.populate(installed_apps)
            wsgi_dot_path = getattr(settings, 'WSGI_APPLICATION', None)
            self.application = HendrixDeploy.importWSGI(wsgi_dot_path)

        self.is_secure = self.options['key'] and self.options['cert']

        self.servers = []

    @classmethod
    def importWSGI(cls, wsgi_dot_path):
        try:
            wsgi_module, application_name = wsgi_dot_path.rsplit('.', 1)
        except AttributeError:
            pid = os.getpid()
            chalk.red(
                "Unable to discern a WSGI application from '%s'" %
                wsgi_dot_path
            )
            os.kill(pid, 15)
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

    def run(self):
        "sets up the desired services and runs the requested action"
        self.addServices()
        self.catalogServers(self.hendrix)
        action = self.action
        fd = self.options['fd']

        if action.startswith('start'):
            chalk.blue(
                'Ready and Listening on port %d...' % self.options.get(
                    'http_port'
                )
            )
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
        _args = [
            'hx',
            'start',  # action

            # kwargs
            '--http_port', str(self.options['http_port']),
            '--https_port', str(self.options['https_port']),
            '--cache_port', str(self.options['cache_port']),
            '--workers', '0',
            '--fd', pickle.dumps(self.fds),
        ]

        # args/signals
        if self.options['dev']:
            _args.append('--dev')
        if self.options['traceback']:
            _args.append('--traceback')

        if not self.use_settings:
            _args += ['--wsgi', self.options['wsgi']]
        return _args

    def addGlobalServices(self):
        """
        This is where we put service that we don't want to be duplicated on
        worker subprocesses
        """
        pass

    def start(self, fd=None):
        if fd is None:
            # anything in this block is only run once
            self.addGlobalServices()
            self.hendrix.startService()
            self.launchWorkers()
        else:
            fds = pickle.loads(fd)
            factories = {}
            for name in self.servers:
                factory = self.disownService(name)
                factories[name] = factory
            self.hendrix.startService()
            for name, factory in factories.iteritems():
                self.addSubprocesses(fds, name, factory)

    def launchWorkers(self):
        pids = [str(os.getpid())]  # script pid
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
                    None, 'hx', args, childFDs=childFDs, env=environ
                )
                transports.append(transport)
                pids.append(str(transport.pid))
        with open(self.pid, 'w') as pid_file:
            pid_file.write('\n'.join(pids))

    def addSubprocesses(self, fds, name, factory):
        self.reactor.adoptStreamPort(  # outputs port
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
