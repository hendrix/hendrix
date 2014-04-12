from hendrix.services import TCPServer
from twisted.web import server, proxy


class ReverseProxyService(TCPServer):

    def __init__(self, host, from_port, to_port, host, path, *args, **kwargs):
        resource = proxy.ReverseProxyResource(host, to_port, path)
        factory = server.Site(resource)
        TCPServer.__init__(self, from_port, factory)
