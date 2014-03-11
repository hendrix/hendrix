from twisted.application import internet, service
from twisted.internet import reactor
from twisted.python.threadpool import ThreadPool
from twisted.web import server, resource, static
from twisted.web.wsgi import WSGIResource
from twisted.web.resource import ForbiddenResource


def get_hendrix_resource(application, settings_module=None, port=80, additional_handlers=None):
    '''
    Pseudo factory that returns the proper Resource object.
    Takes a deployment type and (for development) a port number.
    Returns a tuple (Twisted Resource, Twisted Service)
    '''
    # Create and start a thread pool,
    threads = ThreadPool()

    # The pool will stop when the reactor shuts down
    reactor.addSystemEventTrigger('after', 'shutdown', threads.stop)

    hendrix_server = service.MultiService()

    # Use django's WSGIHandler to create the resource.
    hendrix_resource = WSGIResource(reactor, threads, application)
    root = Root(hendrix_resource)
    if settings_module is not None:
        static_resource = MediaResource(settings_module.STATIC_ROOT)
        root.putChild(settings_module.STATIC_URL.strip('/'), static_resource)
    
    if additional_handlers:
        # additional_handlers should be a list of tuples like: ('/namespace/chat', <chathandler object>)
        for path,handler in additional_handlers:
            root.putChild(path, handler)
            print 'child handler %r listening at /%s'%(handler, path)

    main_site = server.Site(root)

    tcp_service = internet.TCPServer(port, main_site)
    threads_service = ThreadPoolService(threads)

    threads_service.setServiceParent(hendrix_server)
    tcp_service.setServiceParent(hendrix_server)


    return hendrix_resource, hendrix_server


def threadPoolService(reactor=reactor):
    """
    This is a helper function that adds a ThreadPool to the reactor (i.e. the
    event loop) and ensures that those threads are stopped after the reactor
    shuts down. It returns a Service instance such that the thread pool can be
    added to a MultiService instance.
    """
    # Create and start a thread pool,
    threads = ThreadPool()

    # The pool will stop when the reactor shuts down
    reactor.addSystemEventTrigger('after', 'shutdown', threads.stop)

    return ThreadPoolService(threads)


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


class Root(resource.Resource):
    """
    A wrapper that overrides the getChild method on Resource so to only serve
    the WSGIResource
    """

    def __init__(self, wsgi_resource):
        resource.Resource.__init__(self)
        self.wsgi_resource = wsgi_resource

    def getChild(self, name, request):
        """
        Here getChild is only evaluated once. Prepath must be an empty list
        otherwise the WSGIRequest path variable is the combination of the
        prepath and postpath lists. Postpath needs to contain all segments of
        the url, if it is incomplete then that incomplete url with be passed on
        to the child resource (in this case our wsgi application).
        """
        print name

        request.prepath = []
        request.postpath.insert(0, name)

        return self.wsgi_resource


class MediaResource(static.File):
    '''
    A simple static service with directory listing disabled
    (gives the client a 403 instead of letting them browse
    a static directory).
    '''
    def directoryListing(self):
        # Override to forbid directory listing
        return ForbiddenResource()

