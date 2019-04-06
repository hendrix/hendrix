import importlib
import os
import pickle
import shutil
import time
from os import environ
from socket import AF_INET

import autobahn
import chalk
from twisted.application.internet import TCPServer, SSLServer
from twisted.internet import reactor
from twisted.internet.defer import DeferredLock
from twisted.python.threadpool import ThreadPool

from hendrix import defaults
from hendrix.facilities.gather import get_additional_resources, get_additional_services
from hendrix.facilities.protocols import DeployServerProtocol
from hendrix.facilities.services import HendrixService, HendrixTCPService
from hendrix.options import options as hx_options
from hendrix.utils import get_pid, import_string, PID_DIR


class HendrixDeploy(object):
    """
    HendrixDeploy encapsulates the necessary information needed to deploy
    the HendrixService on a single or multiple processes.
    """

    def __init__(self, action='start', options={},
                 reactor=reactor, threadpool=None):
        self.action = action
        self.options = hx_options()
        self.options.update(options)
        self.services = []
        self.resources = []
        self.reactor = reactor

        self.threadpool = threadpool or ThreadPool(name="Hendrix Web Service")

        self.use_settings = True
        # because running the management command overrides self.options['wsgi']
        if self.options['wsgi']:
            if hasattr(self.options['wsgi'], '__call__'):
                # If it has a __call__, we assume that it is the application
                # object itself.
                self.application = self.options['wsgi']
                try:
                    self.options['wsgi'] = "%s.%s" % (
                        self.application.__module__, self.application.__name__
                    )
                except AttributeError:
                    self.options['wsgi'] = self.application.__class__.__name__
            else:
                # Otherwise, we'll try to discern an application in the belief
                # that this is a dot path.
                wsgi_dot_path = self.options['wsgi']
                # will raise AttributeError if we can't import it.
                self.application = HendrixDeploy.importWSGI(wsgi_dot_path)
            self.use_settings = False
        else:
            os.environ['DJANGO_SETTINGS_MODULE'] = self.options['settings']
            settings = import_string('django.conf.settings')
            self.services = get_additional_services(settings)
            self.resources = get_additional_resources(settings)
            self.options = HendrixDeploy.getConf(settings, self.options)

        if self.use_settings:
            django = importlib.import_module('django')
            if django.VERSION[:2] >= (1, 7):
                django.setup()
            wsgi_dot_path = getattr(settings, 'WSGI_APPLICATION', None)
            self.application = HendrixDeploy.importWSGI(wsgi_dot_path)

        self.is_secure = self.options['key'] and self.options['cert']

        self.servers = []
        self._lock = DeferredLock()

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
        try:
            wsgi = importlib.import_module(wsgi_module)
        except ImportError:
            chalk.red("Unable to Import module '%s'\n" % wsgi_dot_path)
            raise
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

    def addGlobalServices(self):
        """
        This is where we put service that we don't want to be duplicated on
        worker subprocesses
        """
        pass

    def getThreadPool(self):
        '''
        Case to match twisted.internet.reactor
        '''
        return self.threadpool

    def addHendrix(self):
        '''
        Instantiates a HendrixService with this object's threadpool.
        It will be added as a service later.
        '''
        self.hendrix = HendrixService(
            self.application,
            threadpool=self.getThreadPool(),
            resources=self.resources,
            services=self.services,
            loud=self.options['loud']
        )
        if self.options["https_only"] is not True:
            self.hendrix.spawn_new_server(self.options['http_port'], HendrixTCPService)

    def catalogServers(self, hendrix):
        "collects a list of service names serving on TCP or SSL"
        for service in hendrix.services:
            if isinstance(service, (TCPServer, SSLServer)):
                self.servers.append(service.name)

    def _listening_message(self):
        message = "non-TLS listening on port {}".format(self.options['http_port'])
        return message

    def run(self):
        "sets up the desired services and runs the requested action"
        self.addServices()
        self.catalogServers(self.hendrix)
        action = self.action
        fd = self.options['fd']

        if action.startswith('start'):
            chalk.blue(self._listening_message())
            getattr(self, action)(fd)

            ###########################
            # annnnd run the reactor! #
            ###########################
            try:
                self.reactor.run()
            finally:
                shutil.rmtree(PID_DIR, ignore_errors=True)  # cleanup tmp PID dir

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

        if not self.use_settings:
            _args += ['--wsgi', self.options['wsgi']]
        return _args

    def start(self, fd=None):
        if fd is None:
            # anything in this block is only run once
            self.addGlobalServices()
            self.hendrix.startService()
            pids = [str(os.getpid())]  # script pid
            if self.options['workers']:
                self.launchWorkers(pids)
            self.pid_file = self.openPidList(pids)
        else:
            fds = pickle.loads(fd)
            factories = {}
            for name in self.servers:
                factory = self.disownService(name)
                factories[name] = factory
            self.hendrix.startService()
            for name, factory in factories.iteritems():
                self.addSubprocess(fds, name, factory)
            chalk.eraser()
            chalk.blue('Starting Hendrix...')

    def setFDs(self):
        """
        Iterator for file descriptors.
        Seperated from launchworkers for clarity and readability.
        """
        # 0 corresponds to stdin, 1 to stdout, 2 to stderr
        self.childFDs = {0: 0, 1: 1, 2: 2}
        self.fds = {}
        for name in self.servers:
            self.port = self.hendrix.get_port(name)
            fd = self.port.fileno()
            self.childFDs[fd] = fd
            self.fds[name] = fd

    def launchWorkers(self, pids):
        # Create a new listening port and several other processes to
        # help out.
        self.setFDs()
        args = self.getSpawnArgs()
        transports = []
        for i in range(self.options['workers']):
            time.sleep(0.05)
            transport = self.reactor.spawnProcess(
                DeployServerProtocol(args), 'hx', args, childFDs=self.childFDs, env=environ
            )
            transports.append(transport)
            pids.append(str(transport.pid))

    def openPidList(self, pids):
        with open(self.pid, 'w') as pid_file:
            pid_file.write('\n'.join(pids))
        return pid_file

    def addSubprocess(self, fds, name, factory):
        """
        Public method for _addSubprocess.
        Wraps reactor.adoptStreamConnection in 
        a simple DeferredLock to guarantee
        workers play well together.
        """
        self._lock.run(self._addSubprocess, self, fds, name, factory)

    def _addSubprocess(self, fds, name, factory):
        self.reactor.adoptStreamConnection(
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
        chalk.green('Stopping Hendrix...')

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

    def add_non_tls_websocket_service(self, websocket_factory):
        autobahn.twisted.websocket.listenWS(websocket_factory)
