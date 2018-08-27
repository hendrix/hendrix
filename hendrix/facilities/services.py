from OpenSSL import SSL
from OpenSSL.crypto import get_elliptic_curve
from twisted.application import internet, service
from twisted.internet import reactor
from twisted.internet import ssl
from twisted.logger import Logger
from twisted.python.threadpool import ThreadPool
from twisted.web import server

from hendrix.facilities.resources import HendrixResource


class HendrixService(service.MultiService):
    """
    HendrixService is a constructor that facilitates the collection of services
    and the extension of resources on the website by subclassing MultiService.
    'application' refers to a WSGI application object: likely a django.core.handlers.wsgi.WSGIHandler
    'resources' refers to a list of Resources with a namespace attribute
    'services' refers to a list of twisted Services to add to the collection.
    """

    log = Logger()

    def __init__(
            self,
            application,
            threadpool=None,
            resources=None,
            services=None,
            loud=False):
        service.MultiService.__init__(self)

        # Create, start and add a thread pool service, which is made available
        # to our WSGIResource within HendrixResource
        if not threadpool:
            self.threadpool = ThreadPool(name="HendrixService")
        else:
            self.threadpool = threadpool

        reactor.addSystemEventTrigger('after', 'shutdown', self.threadpool.stop)
        ThreadPoolService(self.threadpool).setServiceParent(self)

        # create the base resource and add any additional static resources
        resource = HendrixResource(reactor, self.threadpool, application, loud=loud)
        if resources:
            resources = sorted(resources, key=lambda r: r.namespace)
            for res in resources:
                if hasattr(res, 'get_resources'):
                    for sub_res in res.get_resources():
                        resource.putNamedChild(sub_res)
                else:
                    resource.putNamedChild(res)

        self.site = server.Site(resource)

    def spawn_new_server(self, port, server_class, additional_services=None, *args, **kwargs):

        main_web_tcp = server_class(port, self.site, *args, **kwargs)
        main_web_tcp.setName('main_web_tcp')

        # to get this at runtime use
        # hedrix_service.getServiceNamed('main_web_tcp')
        main_web_tcp.setServiceParent(self)

        # add any additional services
        if additional_services:
            for srv_name, srv in additional_services:
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


from twisted.internet.ssl import DefaultOpenSSLContextFactory


class ContextWithECC(SSL.Context):

    def use_privatekey(self, _private_key):
        # At some point, we hope to use PyOpenSSL tooling to do this.  See #144.
        from OpenSSL._util import lib as _OpenSSLlib
        use_result = _OpenSSLlib.SSL_CTX_use_PrivateKey(self._context, _private_key._evp_pkey)
        if not use_result:
            self._raise_passphrase_exception()


class SpecifiedCurveContextFactory(DefaultOpenSSLContextFactory):

    def __init__(self, private_key, cert, curve_name=None, *args, **kwargs):
        DefaultOpenSSLContextFactory.__init__(self, private_key, cert, *args, **kwargs)
        self.set_curve(curve_name)

    def set_curve(self, curve_name):
        curve = get_elliptic_curve(curve_name)
        self._context.set_tmp_ecdh(curve)


class ExistingKeyTLSContextFactory(SpecifiedCurveContextFactory):
    _context = None

    def __init__(self, private_key, cert, curve_name=None,
                 sslmethod=SSL.SSLv23_METHOD, _contextFactory=ContextWithECC):
        self._private_key = private_key
        self.curve_name = curve_name
        self.certificate = cert
        self.sslmethod = sslmethod
        self._contextFactory = _contextFactory
        self.cacheContext()
        self.set_curve(curve_name)

    def cacheContext(self):
        if self._context is None:
            ctx = self._contextFactory(self.sslmethod)
            ctx.set_options(SSL.OP_NO_SSLv2)  # No allow v2.  Obviously.
            ctx.use_certificate(self.certificate)
            ctx.use_privatekey(self._private_key)
            self._context = ctx


class HendrixTCPService(internet.TCPServer):

    def __init__(self, port, site, *args, **kwargs):
        internet.TCPServer.__init__(self, port, site, *args, **kwargs)
        self.site = site


class HendrixTCPServiceWithTLS(internet.SSLServer):

    def __init__(self, port, site, private_key, cert, context_factory=None, context_factory_kwargs=None):
        context_factory = context_factory or ssl.DefaultOpenSSLContextFactory
        context_factory_kwargs = context_factory_kwargs or {}

        self.tls_context = context_factory(
            private_key,
            cert,
            **context_factory_kwargs
        )
        internet.SSLServer.__init__(
            self,
            port,  # integer port
            site,  # our site object, see the web howto
            contextFactory=self.tls_context
        )

        self.site = site
