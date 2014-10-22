from .base import HendrixDeploy

from hendrix.contrib import ssl
from twisted.internet.ssl import PrivateCertificate
from twisted.protocols.tls import TLSMemoryBIOFactory


class HendrixDeploySSL(HendrixDeploy):
    """
    HendrixDeploy encapsulates the necessary information needed to deploy the
    HendrixService on a single or multiple processes.
    """

    def addServices(self):
        """
        a helper function used in HendrixDeploy.run
        it instanstiates the HendrixService and adds child services
        note that these services will also be run on all processes
        """
        super(HendrixDeploySSL, self).addServices()
        self.addSSLService()

    def addSSLService(self):
        "adds a SSLService to the instaitated HendrixService"
        https_port = self.options['https_port']
        key = self.options['key']
        cert = self.options['cert']

        _tcp = self.hendrix.getServiceNamed('main_web_tcp')
        factory = _tcp.factory

        _ssl = ssl.SSLServer(https_port, factory, key, cert)

        _ssl.setName('main_web_ssl')
        _ssl.setServiceParent(self.hendrix)

    def addSubprocesses(self, fds, name, factory):
        super(HendrixDeploySSL, self).addSubprocesses(fds, name, factory)
        if name == 'main_web_ssl':
            privateCert = PrivateCertificate.loadPEM(
                open(self.options['cert']).read() + open(self.options['key']).read()
            )
            factory = TLSMemoryBIOFactory(
                privateCert.options(), False, factory
            )

    def getSpawnArgs(self):
        args = super(HendrixDeploySSL, self).getSpawnArgs()
        args += [
            '--key', self.options.get('key'),
            '--cert', self.options.get('cert')
        ]
        return args
