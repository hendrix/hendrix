from twisted.application.internet import TCPServer
from .factory import CacheFactory


class CacheServer(TCPServer):

    def __init__(self, port, *args, **kwargs):
        factory = CacheFactory()
        TCPServer.__init__(port, factory)
