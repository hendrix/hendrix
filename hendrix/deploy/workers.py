from .base import HendrixDeploy
from hendrix.options import options as hx_options
from twisted.internet import reactor


def deployworkers(action, options, func):
    # Create a new listening port and several other processes to
    # help out.
    fds = {}
    deployer = WorkersDeploy(action, options)
    deployer.fdssetter()
#    args = deployer.getSpawnArgs()
    transports = []
    for i in range(options['workers']):
        transport = func(action, options)
        transports.append(transport)
        pids.append(str(transport.pid))

class WorkersDeploy(HendrixDeploy):
    
    def __init__(self, action='start', options={}, reactor=reactor):
        self.action = action
        self.options = hx_options()
        self.options.update(options)
        self.services = []
        self.resources = []
        self.reactor = reactor
        self.fds ={}

#        self.use_settings = True
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


    def fdssetter(self):
        for name in self.servers:
            port = self.hendrix.get_port(name)
            fd = port.fileno()
            childFDs[fd] = fd
            self.fds[name] = fd

    def start(self):
        fds = pickle.loads(fd)
        factories = {}
        for name in self.servers:
            factory = self.disownService(name)
            factories[name] = factory
        self.hendrix.startService()
        for name, factory in factories.iteritems():
            self.addSubprocesses(fds, name, factory)


    def launchWorkers(self, pids):
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
