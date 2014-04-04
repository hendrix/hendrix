from twisted.web import http
from .protocol import CacheReverseProxy

class CacheFactory(http.HTTPFactory):
    """
    This is the interface for the TCPServer. It overrides the buildProtocol
    method so to create an instance of ReverseProxyRequest which is then
    passed on to the intended server.
    """

    def buildProtocol(self, addr):
        return CacheReverseProxy()
