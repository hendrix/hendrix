import cStringIO
from datetime import datetime
import gzip
import urlparse

from hendrix.defaults import DEFAULT_MAX_AGE

from urllib import quote as urlquote
from time import strptime
from twisted.internet import reactor, defer, threads
from twisted.web import proxy, resource, client
from twisted.web.server import NOT_DONE_YET

PREFIX = "/CACHE"


def processURI(uri, prefix=''):
    """
    helper function to return just the path (uri) and whether or not it's busted
    """
    components = urlparse.urlparse(uri)
    query = dict(urlparse.parse_qsl(components.query))
    bust = True
    bust &= bool(query)  # bust the cache if the query has stuff in it
    bust &= query.get('cache') != 'true'  # bust the cache if the query key 'cache' isn't true
    return prefix + components.path, bust


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

    def closeBuffer(self):
        self.buffer.close()

    def connectionMade(self):
        proxy.ProxyClient.connectionMade(self)

    def connectionLost(self, reason):
        proxy.ProxyClient.connectionLost(self, reason)

    def dataReceived(self, transport):
        proxy.ProxyClient.dataReceived(self, transport)

    def handleHeader(self, key, value):
        "extends handleHeader to save headers to a local response object"
        if key.lower() == 'location':
            value = self.modLocationPort(value, 8000)
        proxy.ProxyClient.handleHeader(self, key, value)
        self._response.headers[key.lower()] = value

    def handleStatus(self, version, code, message):
        "extends handleStatus to instantiate a local response object"
        # if int(code) != 301:
        proxy.ProxyClient.handleStatus(self, version, code, message)
        # client.Response is currently just a container for needed data
        self._response = client.Response(version, code, message, {}, None)

    def modLocationPort(self, location, port):
        "ensures that the location port is a the given port value"
        components = urlparse.urlparse(location)
        _value = getattr(components, 'port')
        if _value != port:
            _components = components._asdict()  # returns an ordered dict of urlparse.ParseResult components
            _components['netloc'] = '%s:%d' % (components.hostname, port)
        return urlparse.urlunparse(_components.values())

    def handleResponseEnd(self):
        """
        Extends handleResponseEnd to not care about the user closing/refreshing
        their browser before the response is finished. Also calls cacheContent
        in a thread that we don't care when it finishes.
        """
        try:
            if not self._finished:
                content = self.buffer.getvalue()
                reactor.callInThread(self.cacheContent, content, self.father)
            proxy.ProxyClient.handleResponseEnd(self)
        except RuntimeError:
            # because we don't care if the user hits
            # refresh before the request is done
            pass

    def cacheContent(self, content, request):
        """
        Caches the content in a gzipped format given that a `cache_it` flag is
        True
        """
        code = int(self._response.code)
        cache_it = False
        # only cache the content if it was successful and requested using GET
        uri, bust = processURI(request.uri, PREFIX)
        if request.method == "GET" and code/100 == 2 and not bust:
            cache_control = self._response.headers.get('cache-control')
            if cache_control:
                params = dict(urlparse.parse_qsl(cache_control))
                if int(params.get('max-age', '0')) > 0:
                    cache_it = True
            if cache_it:
                content = self.compressBuffer(content)
                self.resource.putCache(content, uri, self._response.headers)
        self.closeBuffer()


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

    isLeaf = True

    def __init__(self, content=None, headers=None):
        resource.Resource.__init__(self)
        self.content = content
        self.headers = headers
        self.created = datetime.now()

    def decompressBuffer(self, buffer):
        "complements the compressBuffer function in CacheClient"
        zbuf = cStringIO.StringIO(buffer)
        zfile = gzip.GzipFile(fileobj=zbuf)
        deflated = zfile.read()
        zfile.close()
        return deflated

    def decompressContent(self):
        self.content = self.decompressBuffer(self.content)

    def render(self, request):
        return self.content

    def getMaxAge(self):
        "get the max-age in seconds from the saved headers data"
        max_age = 0
        cache_control = self.headers.get('cache_control')
        if cache_control:
            params = dict(urlparse.parse_qsl(cache_control))
            max_age = int(params.get('max-age', '0'))
        return max_age

    def convertTimeString(self, timestr):
        """
        Returns a datetime instance from a str formatted as follows
            e.g. 'Mon, 03 Mar 2014 12:12:12 GMT'
        """
        time_struc = strptime(timestr, '%a, %d %b %Y %H:%M:%S GMT')
        return datetime(*time_struc[:6])

    def getLastModified(self):
        "returns the GMT last-modified datetime or None"
        last_modified = self.headers.get('last-modified')
        if last_modified:
            last_modified = self.convertTimeString(last_modified)
        return last_modified

    def getDate(self):
        "returns the GMT response datetime or None"
        date = self.headers.get('date')
        if date:
            date = self.convertTimeString(date)
        return date

    def isFresh(self):
        "returns True if cached object is still fresh"
        max_age = self.getMaxAge()
        date = self.getDate()
        is_fresh = False
        if max_age and date:
            delta_time = datetime.now() - date
            is_fresh = delta_time.total_seconds() < max_age
        return is_fresh

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

    def getChildWithDefault(self, path, request):
        """
        Retrieve a static or dynamically generated child resource from me.
        """
        # start caching logic
        is_secure = request.isSecure()
        uri, bust = processURI(request.uri, PREFIX)  # the prefix namespaces these resources
        # Reasons not to bother looking in the Cache
        #     * it's been busted
        #     * it's a secure request
        #     * it's not a GET request
        #     * it's not actually in the cache
        if uri in self.children and not is_secure and request.method == "GET" and not bust:
            child = self.children[uri]
            is_fresh = child.isFresh()
            if is_fresh:
                encodings = request.getHeader('accept-encoding')
                if encodings and 'gzip' in encodings:
                    request.responseHeaders.addRawHeader('content-encoding', 'gzip')
                    request.responseHeaders.addRawHeader('content-length', len(child.content))
                else:
                    child.decompressContent()
                return child
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

    def decompressBuffer(self, buffer):
        "complements the compressBuffer function in CacheClient"
        zbuf = cStringIO.StringIO(buffer)
        zfile = gzip.GzipFile(fileobj=zbuf)
        deflated = zfile.read()
        zfile.close()
        return deflated

    def decompressContent(self):
        self.content = self.decompressBuffer(self.content)

    def getGlobalSelf(self):
        """
        This searches the reactor for the original instance of CacheProxyResource.
        This is necessary because with each call of getChild a new instance of
        CacheProxyResource is created.
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

    def putCache(self, content, url, headers):
        """
        instantiates the CachedResource and adds to the global
        ReverseProxyResource children
        """
        resource = CachedResource(content, headers)
        self.putChild(url, resource)
