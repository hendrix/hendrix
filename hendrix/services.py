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

    def __init__(self, application, port=80, resources=None, services=None, host=None):
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


        # create the base server/client
        factory = server.Site(resource)
        if host:
            factory = protocol.ReconnectingClientFactory(factory)
            internet.TCPClient(host, port, factory).setServiceParent(self)
        else:
            # add a tcp server that binds to port=port
            internet.TCPServer(port, factory).setServiceParent(self)

        # add any additional services
        if services:
            for srv in services:
                srv.setServiceParent(self)



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
              'apps.offload.services.TimeService',
            )
    """

    additional_services = []

    if hasattr(settings_module, 'HENDRIX_SERVICES'):
        for module_path in settings_module.HENDRIX_SERVICES:
            path_to_module, service_name = module_path.rsplit('.', 1)
            resource_module = importlib.import_module(path_to_module)

            additional_services.append(getattr(resource_module, service_name))
    return additional_services
