import chalk
from autobahn.twisted.websocket import listenWS
from twisted.internet import reactor
from twisted.internet.ssl import PrivateCertificate, DefaultOpenSSLContextFactory
from twisted.protocols.tls import TLSMemoryBIOFactory

from hendrix.facilities.services import HendrixTCPServiceWithTLS
from .base import HendrixDeploy


class HendrixDeployTLS(HendrixDeploy):
    """
    A HendrixDeploy that listens only via TLS.

    This class can accept a key and certificate combination and can
    also pass arbitrary kwargs to the SSLContextFactory which
    governs it use.

    Notice that there's no hazmat here.  For the main service, all of the TLS is done
    through Twisted (and thus PyOpenSSL) via the HendrixTCPServiceWithTLS
    class, which is worth a look if you're interested in how this thing is
    secured.
    """

    def __init__(self, action='start', options={},
                 reactor=reactor, threadpool=None,
                 key=None, cert=None, context_factory=None,
                 context_factory_kwargs=None,
                 *args, **kwargs):

        super(HendrixDeployTLS, self).__init__(action, options, reactor, threadpool,
                                               *args, **kwargs)
        if options.get("https_port") and not options.get("http_port"):
            self.options["https_only"] = True
        key = key or self.options['key']
        cert = cert or self.options['cert']
        if not (key and cert):
            raise ValueError("Can't launch with TLS unless you pass a valid key and cert.")
        self.key = key
        self.cert = cert

        if context_factory is None:
            self.context_factory = DefaultOpenSSLContextFactory
        else:
            self.context_factory = context_factory

        if context_factory_kwargs is None:
            self.context_factory_kwargs = {}
        else:
            self.context_factory_kwargs = context_factory_kwargs

    def addServices(self):
        """
        a helper function used in HendrixDeploy.run
        it instanstiates the HendrixService and adds child services
        note that these services will also be run on all processes
        """
        super(HendrixDeployTLS, self).addServices()
        self.addSSLService()

    def addSSLService(self):
        "adds a SSLService to the instaitated HendrixService"
        https_port = self.options['https_port']
        self.tls_service = HendrixTCPServiceWithTLS(https_port, self.hendrix.site, self.key, self.cert,
                                                    self.context_factory, self.context_factory_kwargs)
        self.tls_service.setServiceParent(self.hendrix)

    def addSubprocesses(self, fds, name, factory):
        super(HendrixDeployTLS, self).addSubprocesses(fds, name, factory)
        if name == 'main_web_ssl':
            privateCert = PrivateCertificate.loadPEM(
                open(self.options['cert']).read() + open(self.options['key']).read()
            )
            factory = TLSMemoryBIOFactory(
                privateCert.options(), False, factory
            )

    def getSpawnArgs(self):
        args = super(HendrixDeployTLS, self).getSpawnArgs()
        args += [
            '--key', self.options.get('key'),
            '--cert', self.options.get('cert')
        ]
        return args

    def _listening_message(self):
        message = "TLS listening on port {}".format(self.options['https_port'])
        if self.options['https_only'] is not True:
            message += " and non-TLS on port {}".format(self.options['http_port'])
        return message

    def _add_tls_websocket_service_after_running(self, websocket_factory, *args, **kwargs):
        chalk.blue("TLS websocket listener on port {}".format(websocket_factory.port))
        listenWS(factory=websocket_factory, contextFactory=self.tls_service.tls_context, *args, **kwargs)

    def add_tls_websocket_service(self, websocket_factory, *args, **kwargs):
        self.reactor.callWhenRunning(self._add_tls_websocket_service_after_running, websocket_factory, *args, **kwargs)
