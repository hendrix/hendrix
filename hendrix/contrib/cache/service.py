from .resource import ReverseProxyResource

from hendrix.services import TCPServer
from twisted.web import server, proxy


class CacheService(TCPServer):

    def __init__(self, proxy_port, site_port, *args, **kwargs):
        resource = ReverseProxyResource(site_port)
        factory = server.Site(resource)
        TCPServer.__init__(self, proxy_port, factory)
