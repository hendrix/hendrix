try:
    import cStringIO
except ImportError:
    from io import BytesIO as cStringIO

try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse

from twisted.internet import reactor
from twisted.web import proxy, client
from twisted.web.server import NOT_DONE_YET

from hendrix.utils import responseInColor
from . import decompressBuffer
from .backends.memory_cache import MemoryCacheBackend

try:
    from urllib import quote as urlquote
except ImportError:
    from urllib.parse import quote as urlquote


class CacheClient(proxy.ProxyClient):
    """
    SHOW ME THE CACHE BABY!
    """

    def __init__(self, command, rest, version, headers, data, father, resource):
        proxy.ProxyClient.__init__(
            self, command, rest, version, headers, data, father
        )
        self.resource = resource
        self.buffer = cStringIO.StringIO()
        self._response = None

    def handleHeader(self, key, value):
        "extends handleHeader to save headers to a local response object"
        key_lower = key.lower()
        if key_lower == 'location':
            value = self.modLocationPort(value)
        self._response.headers[key_lower] = value
        if key_lower != 'cache-control':
            # This causes us to not pass on the 'cache-control' parameter
            # to the browser
            # TODO: we should have a means of giving the user the option to
            # configure how they want to manage browser-side cache control
            proxy.ProxyClient.handleHeader(self, key, value)

    def handleStatus(self, version, code, message):
        "extends handleStatus to instantiate a local response object"
        proxy.ProxyClient.handleStatus(self, version, code, message)
        # client.Response is currently just a container for needed data
        self._response = client.Response(version, code, message, {}, None)

    def modLocationPort(self, location):
        """
        Ensures that the location port is a the given port value
        Used in `handleHeader`
        """
        components = urlparse.urlparse(location)
        reverse_proxy_port = self.father.getHost().port
        reverse_proxy_host = self.father.getHost().host
        # returns an ordered dict of urlparse.ParseResult components
        _components = components._asdict()
        _components['netloc'] = '%s:%d' % (
            reverse_proxy_host, reverse_proxy_port
        )
        return urlparse.urlunparse(_components.values())

    def handleResponseEnd(self):
        """
        Extends handleResponseEnd to not care about the user closing/refreshing
        their browser before the response is finished. Also calls cacheContent
        in a thread that we don't care when it finishes.
        """
        try:
            if not self._finished:
                reactor.callInThread(
                    self.resource.cacheContent,
                    self.father,
                    self._response,
                    self.buffer
                )
            proxy.ProxyClient.handleResponseEnd(self)
        except RuntimeError:
            # because we don't care if the user hits
            # refresh before the request is done
            pass

    def handleResponsePart(self, buffer):
        """
        Sends the content to the browser and keeps a local copy of it.
        buffer is just a str of the content to be shown, father is the intial
        request.
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
        zfile = gzip.GzipFile(mode='wb', fileobj=zbuf, compresslevel=9)
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
        return self.protocol(
            self.command, self.rest, self.version,
            self.headers, self.data, self.father, self.resource
        )


class CacheProxyResource(proxy.ReverseProxyResource, MemoryCacheBackend):
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
        This is necessary because the parent class would call
        proxy.ReverseProxyResource instead of CacheProxyResource
        """
        return CacheProxyResource(
            self.host, self.port, self.path + '/' + urlquote(path, safe=""),
            self.reactor
        )

    def getChildWithDefault(self, path, request):
        """
        Retrieve a static or dynamically generated child resource from me.
        """
        cached_resource = self.getCachedResource(request)
        if cached_resource:
            reactor.callInThread(
                responseInColor,
                request,
                '200 OK',
                cached_resource,
                'Cached',
                'underscore'
            )
            return cached_resource
        # original logic
        if path in self.children:
            return self.children[path]
        return self.getChild(path, request)

    def render(self, request):
        """
        Render a request by forwarding it to the proxied server.
        """
        # set up and evaluate a connection to the target server
        if self.port == 80:
            host = self.host
        else:
            host = "%s:%d" % (self.host, self.port)
        request.requestHeaders.addRawHeader('host', host)
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

    def decompressContent(self):
        self.content = decompressBuffer(self.content)

    def getGlobalSelf(self):
        """
        This searches the reactor for the original instance of
        CacheProxyResource. This is necessary because with each call of
        getChild a new instance of CacheProxyResource is created.
        """
        transports = self.reactor.getReaders()
        for transport in transports:
            try:
                resource = transport.factory.resource
                if isinstance(resource, self.__class__) and resource.port == self.port:
                    return resource
            except AttributeError:
                pass
        return
