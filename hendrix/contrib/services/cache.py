from twisted.web import server

from hendrix.contrib.cache.resource import CacheProxyResource
from hendrix.facilities.services import HendrixTCPService


class CacheService(HendrixTCPService):

    def __init__(self, host, from_port, to_port, path, *args, **kwargs):
        resource = CacheProxyResource(host, to_port, path)
        factory = server.Site(resource)
        HendrixTCPService.__init__(self, from_port, factory)
