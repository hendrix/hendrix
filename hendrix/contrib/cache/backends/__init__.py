"""
Fuck YEAH. enthusiasm.
"""
try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse

from hendrix.contrib.cache import compressBuffer, decompressBuffer

PREFIX = "/CACHE"


class CacheBackend(object):
    "The api to use when creating a cache backend"

    @property
    def cache(self):
        """
        `cache` is the interface to be used in the addResource and
        resourceExists methods.
        """
        raise NotImplementedError(
            'You need to override the "cache" method before implementing'
            'the cache backend'
        )

    def addResource(self, content, uri, headers):
        """
        Adds the a hendrix.contrib.cache.resource.CachedResource to the
        ReverseProxy cache connection
        """
        raise NotImplementedError(
            'You need to override the "addResource" method before implementing'
            'the cache backend'
        )

    def getResource(self, uri):
        """
        Returns a hendrix.contrib.cache.resource.CachedResource from the
        ReverseProxy cache connection
        """
        raise NotImplementedError(
            'You need to override the "addResource" method before implementing'
            'the cache backend'
        )

    def resourceExists(self, uri):
        """
        Returns a boolean indicating whether or not the resource is in the
        cache
        """
        raise NotImplementedError(
            'You need to override "resourceExists" to have your backend work..'
        )

    def processURI(self, uri, prefix=''):
        """
        helper function to return just the path (uri) and whether or not it's
        busted
        """
        components = urlparse.urlparse(uri)
        query = dict(urlparse.parse_qsl(components.query))
        bust = True
        bust &= bool(query)  # bust the cache if the query has stuff in it
        # bust the cache if the query key 'cache' isn't true
        bust &= query.get('cache') != 'true'
        return prefix + components.path, bust

    def cacheContent(self, request, response, buffer):
        """
        Checks if the response should be cached.
        Caches the content in a gzipped format given that a `cache_it` flag is
        True
        To be used CacheClient
        """
        content = buffer.getvalue()
        code = int(response.code)
        cache_it = False
        uri, bust = self.processURI(request.uri, PREFIX)
        # Conditions for adding uri response to cache:
        #     * if it was successful i.e. status of in the 200s
        #     * requested using GET
        #     * not busted
        if request.method == "GET" and code / 100 == 2 and not bust:
            cache_control = response.headers.get('cache-control')
            if cache_control:
                params = dict(urlparse.parse_qsl(cache_control))
                if int(params.get('max-age', '0')) > 0:
                    cache_it = True
            if cache_it:
                content = compressBuffer(content)
                self.addResource(content, uri, response.headers)
        buffer.close()

    def getCachedResource(self, request):
        """
        """
        # start caching logic
        is_secure = request.isSecure()
        # the prefix namespaces these resources
        uri, bust = self.processURI(request.uri, PREFIX)
        # Reasons not to bother looking in the Cache
        #     * it's been busted
        #     * it's a secure request
        #     * it's not a GET request
        #     * it's not actually in the cache
        if not is_secure and request.method == "GET" and not bust:
            if self.resourceExists(uri):
                child = self.getResource(uri)
                is_fresh = child.isFresh()
                if is_fresh:
                    encodings = request.getHeader('accept-encoding')
                    if encodings and 'gzip' in encodings:
                        request.responseHeaders.addRawHeader(
                            'content-encoding', 'gzip'
                        )
                        request.responseHeaders.addRawHeader(
                            'content-length', len(child.content)
                        )
                    else:
                        child = decompressBuffer(child.content)
                    return child
        return None
