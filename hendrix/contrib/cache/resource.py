import cStringIO
from datetime import datetime
import gzip
import urlparse

from urllib import quote as urlquote
from twisted.internet import reactor, defer
from twisted.web import proxy, resource
from twisted.web.server import NOT_DONE_YET



class CacheClient(proxy.ProxyClient):
    """
    SHOW ME THE CACHE BABY!
    """

    def __init__(self, command, rest, version, headers, data, father, resource):
        proxy.ProxyClient.__init__(
            self, command, rest, version, headers, data, father
        )
        self.resource = resource


    def openBuffer(self):
        self.buffer = cStringIO.StringIO()

    def closeBuffer(self):
        self.buffer.close()

    def connectionMade(self):
        proxy.ProxyClient.connectionMade(self)
        self.openBuffer()

    def connectionLost(self, reason):
        proxy.ProxyClient.connectionLost(self, reason)
        self.closeBuffer()
        # print 'hello', reason

    def dataReceived(self, transport):
        proxy.ProxyClient.dataReceived(self, transport)

    def handleResponseEnd(self):
        # try:
        proxy.ProxyClient.handleResponseEnd(self)
        # except RuntimeError:
            # import ipdb; ipdb.set_trace()
            # pass
        # execute cache logic
        # self.cache(buffer, request)

    # def cache(self, buffer, request):
    #     # d = defer.Deferred()
    #
    #     cache_control = self.headers.get('cache-control')
    #     if cache_control:
    #         max_age_name, max_age = urlparse.parse_qsl(cache_control)[0]
    #         max_age = int(max_age)
    #     else:
    #         max_age = MAX_AGE
    #     if max_age and self.father.method == "GET" and self.father.code/100 == 2:
    #         self.resource.putCache(self.father.uri, request)
    #
    #     return d.callback


    def handleResponsePart(self, buffer):
        """
        buffer is just a str of the content to be shown, father is the intial
        request.
        Compresses and stores web responses associated to uri's
        """
        self.father.write(buffer)
        self.buffer.write(buffer)


    def compressBuffer(self, buffer):
        """
        Note that this code compresses into a buffer held in memory, rather
        than a disk file. This is done through the use of cStringIO.StringIO().
        """
        # http://jython.xhaus.com/http-compression-in-python-and-jython/
        zbuf = cStringIO.StringIO()
        zfile = gzip.GzipFile(mode='wb',  fileobj=zbuf, compresslevel=9)
        zfile.write(buffer)
        zfile.close()
        return zbuf.getvalue()



class CacheClientFactory(proxy.ProxyClientFactory):

    protocol = CacheClient

    def __init__(self, command, rest, version, headers, data, father, resource):
        self.command = command
        self.rest = rest
        self.version = version
        self.headers = headers
        self.data = data
        self.father = father
        self.resource = resource

    def buildProtocol(self, addr):
        return self.protocol(self.command, self.rest, self.version,
            self.headers, self.data, self.father, self.resource)



class CachedResource(resource.Resource):


    def __init__(self, content, request):
        resource.Resource.__init__(self)
        self.content = content
        self.request = request

    def render(self, request):
        return self.content



class CacheProxyResource(proxy.ReverseProxyResource):
    """
    This is a state persistent subclass of the built-in ReverseProxyResource.
    """


    def __init__(self, host, to_port, path, reactor=reactor):
        """
        The 'to_port' arg points to the port of the server that we are sending
        a request to
        """
        proxy.ReverseProxyResource.__init__(
            self, host, to_port, path, reactor=reactor
        )
        self.proxyClientFactoryClass = CacheClientFactory

    def getChild(self, path, request):
        """
        This is necessary because the parent class would call proxy.ReverseProxyResource
        instead of CacheProxyResource
        """
        return CacheProxyResource(
            self.host, self.port, self.path + '/' + urlquote(path, safe=""),
            self.reactor
        )

    def render(self, request):
        """
        Render a request by forwarding it to the proxied server.
        """
        # set up and evaluate a connection to the target server
        if self.port == 80:
            host = self.host
        else:
            host = "%s:%d" % (self.host, self.port)
        request.received_headers['host'] = host
        request.content.seek(0, 0)
        qs = urlparse.urlparse(request.uri)[4]
        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path

        global_self = self.getGlobalSelf()

        clientFactory = self.proxyClientFactoryClass(
            request.method, rest, request.clientproto,
            request.getAllHeaders(), request.content.read(), request,
            global_self  # this is new
        )
        self.reactor.connectTCP(self.host, self.port, clientFactory)

        return NOT_DONE_YET

    def decompressBuffer(self, buffer):
        "complements the compressBuffer function in CacheClient"
        zbuf = cStringIO.StringIO(buffer)
        zfile = gzip.GzipFile(fileobj=zbuf)
        deflated = zfile.read()
        zfile.close()
        return deflated

    def getGlobalSelf(self):
        transports = self.reactor.getReaders()
        for transport in transports:
            try:
                resource = transport.factory.resource
                if isinstance(resource, self.__class__) and resource.port == self.port:
                    return resource
            except AttributeError:
                pass
        return



    def putCache(self, url, request):
        content = self.buffer.getvalue()
        resource = CachedResource(content, request)
        self.putChild(url, resource)
