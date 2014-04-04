import sys
import importlib
from .resources import HendrixResource
from twisted.application import internet, service
from twisted.internet import reactor, protocol
from twisted.python.threadpool import ThreadPool
from twisted.web import server, resource, static

import logging

logger = logging.getLogger(__name__)


class HendrixService(service.MultiService):
    """
    HendrixService is a constructor that facilitates the collection of services
    and the extension of resources on the website by subclassing MultiService.
    'application' refers to an instance of django.core.handlers.wsgi.WSGIHandler
    'resources' refers to a list of twisted Resources with a namespace attribute
    'services' refers to a list of twisted Services to add to the collection.
    """

    def __init__(self, application, port=80, resources=None, services=None):
        service.MultiService.__init__(self)

        # Create, start and add a thread pool service, which is made available
        # to our WSGIResource within HendrixResource
        threads = ThreadPool()
        reactor.addSystemEventTrigger('after', 'shutdown', threads.stop)
        ThreadPoolService(threads).setServiceParent(self)

        # create the base resource and add any additional static resources
        resource = HendrixResource(reactor, threads, application)
        if resources:
            for res in resources:
                resource.putNamedChild(res)


        self.factory = server.Site(resource)
        # add a tcp server that binds to port=port
        web_tcp = internet.TCPServer(port, self.factory)
        web_tcp.setName('web_tcp')  # to get this at runtime use hedrix_service.getServiceNamed('web_tcp')
        web_tcp.setServiceParent(self)

        # add any additional services
        if services:
            for srv_nam, srv in services:
                srv.setName(srv_name)
                srv.setServiceParent(self)

    @property
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


def get_additional_services(settings_module):
    """
        if HENDRIX_SERVICES is specified in settings_module,
        it should be a list twisted internet services

        example:

            HENDRIX_SERVICES = (
              ('myServiceName', 'apps.offload.services.TimeService'),
            )
    """

    additional_services = []

    if hasattr(settings_module, 'HENDRIX_SERVICES'):
        for module_path in settings_module.HENDRIX_SERVICES:
            path_to_module, service_name = module_path.rsplit('.', 1)
            resource_module = importlib.import_module(path_to_module)

            additional_services.append(getattr(resource_module, service_name))
    return additional_services
