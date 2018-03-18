from hendrix.facilities.services import HendrixTCPServiceWithTLS
from .base import HendrixDeploy
from twisted.internet.ssl import PrivateCertificate
from twisted.protocols.tls import TLSMemoryBIOFactory
from twisted.internet import reactor


class HendrixDeployTLS(HendrixDeploy):
    """
    HendrixDeploy encapsulates the necessary information needed to deploy the
    HendrixService on a single or multiple processes.
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
        if not key and cert:
            raise ValueError("Can't launch with TLS unless you pass a valid key and cert.")
        self.key = key
        self.cert = cert
        self.context_factory = context_factory
        self.context_factory_kwargs = context_factory_kwargs or {}

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
        tls_service = HendrixTCPServiceWithTLS(https_port, self.hendrix.site, self.key, self.cert,
                             self.context_factory, self.context_factory_kwargs)
        tls_service.setServiceParent(self.hendrix)

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