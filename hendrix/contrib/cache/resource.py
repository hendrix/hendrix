import cStringIO
from datetime import datetime
import gzip
import urlparse

from urllib import quote as urlquote
from twisted.internet import reactor
from twisted.web import proxy
from twisted.web.server import NOT_DONE_YET


# TODO add options to modify the max age of content
MAX_AGE = 3600


# TODO remove the qs from the uri used in the cache ie remove everything after ?



class CacheClient(proxy.ProxyClient):
    """
    SHOW ME THE CACHE BABY!
    """

    def __init__(self, command, rest, version, headers, data, father, resource):
        proxy.ProxyClient.__init__(
            self, command, rest, version, headers, data, father
        )
        self.resource = resource


    def connectionMade(self):
        proxy.ProxyClient.connectionMade(self)


    def dataReceived(self, transport):
        proxy.ProxyClient.dataReceived(self, transport)


    def handleResponsePart(self, buffer):
        """
        buffer is just a str of the content to be shown, father is the intial
        request.
        Compresses and stores web responses associated to uri's
        """
        cache_control = self.headers.get('cache-control', 'max-age=%d' % MAX_AGE)
        max_age_name, max_age = urlparse.parse_qsl(cache_control)[0]
        max_age = int(max_age)
        if max_age:
            self.resource.cache[self.father.uri] = [
                self.compressBuffer(buffer),
                max_age,
                datetime.now()
            ]
        self.father.write(buffer)


    def compressBuffer(self, buffer):
        """
        Note that this code compresses into a buffer held in memory, rather
        than a disk file. This is done through the use of cStringIO.StringIO().
        """
        # http://jython.xhaus.com/http-compression-in-python-and-jython/
        zbuf = cStringIO.StringIO()
        zfile = gzip.GzipFile(mode='wb',  fileobj=zbuf, compresslevel = 9)
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



class ReverseProxyResource(proxy.ReverseProxyResource):
    """
    This is a state persistent subclass of the built-in ReverseProxyResource.
    """

    def __init__(self, site_port, host='localhost', path='', reactor=reactor, secure_port=443):
        proxy.ReverseProxyResource.__init__(
            self, host, site_port, path, reactor=reactor
        )
        self.proxyClientFactoryClass = CacheClientFactory
        self.original_path = self.path
        self.secure_port = secure_port
        self.cache = {}



    def getChild(self, path, request):
        """
        It's important to override this method so to reference the subclass in
        this method, in our case CacheResource, or else the inherited getChild
        method will initialize ReverseProxyResource and therein bypass any
        custom ProxyClient you wish to use.
        """
        self.path = self.path + '/' + urlquote(path, safe="")
        if request.postpath:
            path = request.postpath.pop(0)
            ret = self.getChild(path, request)
        else:
            ret = self
        return ret

    def render(self, request):
        """
        Render a request by forwarding it to the proxied server.
        """

        is_secure = request.isSecure()
        # start caching logic
        if self.path in self.cache and not is_secure:
            content, max_age, created = self.cache[self.path]
            delta_time = datetime.now() - created
            is_fresh = delta_time.total_seconds() < max_age

            if is_fresh:
                self.path = self.original_path
                encodings = request.getHeader('accept-encoding')
                if 'gzip' in encodings:
                    request.responseHeaders.addRawHeader('content-encoding', 'gzip')
                else:
                    content = self.decompressBuffer(content)
                return content

        # set up and evaluate a connection to the target server
        port = self.secure_port if is_secure else self.port
        host = "%s:%d" % (self.host, port)
        request.received_headers['host'] = host
        request.content.seek(0, 0)
        qs = urlparse.urlparse(request.uri)[4]
        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path
        clientFactory = self.proxyClientFactoryClass(
            request.method, rest, request.clientproto,
            request.getAllHeaders(), request.content.read(), request, self)
        self.reactor.connectTCP(self.host, port, clientFactory)

        # reset the path to start from
        self.path = self.original_path
        return NOT_DONE_YET

    def decompressBuffer(self, buffer):
        "complements the compressBuffer function in CacheClient"
        zbuf = cStringIO.StringIO(buffer)
        zfile = gzip.GzipFile(fileobj=zbuf)
        deflated = zfile.read()
        zfile.close()
        return deflated
