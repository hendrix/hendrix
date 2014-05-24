"""
local memory cache backend
"""
from . import CacheBackend
from hendrix.contrib.cache import CachedResource


class MemoryCacheBackend(CacheBackend):

    _cache = {}

    @property
    def cache(self):
        return self._cache

    def addResource(self, content, uri, headers):
        """
        Adds the a hendrix.contrib.cache.resource.CachedResource to the
        ReverseProxy cache connection
        """
        self.cache[uri] = CachedResource(content, headers)

    def resourceExists(self, uri):
        """
        Returns a boolean indicating whether or not the resource is in the
        cache
        """
        return uri in self.cache

    def getResource(self, uri):
        return self.cache[uri]
