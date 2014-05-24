from hendrix.contrib.cache.resource import CacheProxyResource
from hendrix.services import TCPServer
from twisted.web import server


class CacheService(TCPServer):

    def __init__(self, host, from_port, to_port, path, *args, **kwargs):
        resource = CacheProxyResource(host, to_port, path)
        factory = server.Site(resource)
        TCPServer.__init__(self, from_port, factory)
