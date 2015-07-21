from twisted.application import internet, service
from twisted.internet import reactor
from twisted.python.threadpool import ThreadPool
from twisted.web import server

from twisted.logger import Logger
from hendrix.facilities.resources import HendrixResource


class HendrixService(service.MultiService):
    """
    HendrixService is a constructor that facilitates the collection of services
    and the extension of resources on the website by subclassing MultiService.
    'application' refers to a django.core.handlers.wsgi.WSGIHandler
    'resources' refers to a list of Resources with a namespace attribute
    'services' refers to a list of twisted Services to add to the collection.
    """

    log = Logger()

    def __init__(
            self, application, port=80, resources=None, services=None,
            loud=False):
        service.MultiService.__init__(self)

        # Create, start and add a thread pool service, which is made available
        # to our WSGIResource within HendrixResource
        threads = ThreadPool(name="Hendrix Service")

        # Testing threads 1-2-3
        threads.adjustPoolsize(3, 5)

        reactor.addSystemEventTrigger('after', 'shutdown', threads.stop)
        ThreadPoolService(threads).setServiceParent(self)

        # create the base resource and add any additional static resources
        resource = HendrixResource(reactor, threads, application, loud=loud)
        if resources:
            resources = sorted(resources, key=lambda r: r.namespace)
            for res in resources:
                if hasattr(res, 'get_resources'):
                    for sub_res in res.get_resources():
                        resource.putNamedChild(sub_res)
                else:
                    resource.putNamedChild(res)

        factory = server.Site(resource)
        # add a tcp server that binds to port=port
        main_web_tcp = TCPServer(port, factory)
        main_web_tcp.setName('main_web_tcp')
        # to get this at runtime use
        # hedrix_service.getServiceNamed('main_web_tcp')
        main_web_tcp.setServiceParent(self)

        # add any additional services
        if services:
            for srv_name, srv in services:
                srv.setName(srv_name)
                srv.setServiceParent(self)

    def get_port(self, name):
        "Return the port object associated to our tcp server"
        service = self.getServiceNamed(name)
        return service._port

    def add_server(self, name, protocol, server):
        self.servers[(name, protocol)] = server


class ThreadPoolService(service.Service):
    '''
    A simple class that defines a threadpool on init
    and provides for starting and stopping it.
    '''
    def __init__(self, pool):
        "self.pool returns the twisted.python.ThreadPool() instance."
        if not isinstance(pool, ThreadPool):
            msg = '%s must be initialised with a ThreadPool instance'
            raise TypeError(
                msg % self.__class__.__name__
            )
        self.pool = pool

    def startService(self):
        service.Service.startService(self)
        self.pool.start()

    def stopService(self):
        service.Service.stopService(self)
        self.pool.stop()


class TCPServer(internet.TCPServer):

    def __init__(self, port, factory, *args, **kwargs):
        internet.TCPServer.__init__(self, port, factory, *args, **kwargs)
        self.factory = factory
