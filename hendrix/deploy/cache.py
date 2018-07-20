from hendrix.contrib.services.cache import CacheService
from .base import HendrixDeploy


class HendrixDeployCache(HendrixDeploy):
    """
    HendrixDeploy encapsulates the necessary information needed to deploy
    the HendrixService on a single or multiple processes.
    """

    def addServices(self):
        super(HendrixDeployCache, self).addServices()

        if not self.options.get('global_cache') and self.options.get('cache'):
            self.addLocalCacheService()

    def getCacheService(self):
        cache_port = self.options.get('cache_port')
        http_port = self.options.get('http_port')
        return CacheService(
            host='localhost', from_port=cache_port, to_port=http_port, path=''
        )

    def addLocalCacheService(self):
        "adds a CacheService to the instatiated HendrixService"
        _cache = self.getCacheService()
        _cache.setName('cache_proxy')
        _cache.setServiceParent(self.hendrix)

    def getSpawnArgs(self):
        _args = super(HendrixDeployCache, self).getSpawnArgs()
        _args.append('--cache')

        if self.options['global_cache']:
            _args.append('--global_cache')
        return _args

    def addGlobalServices(self):
        """
        This is where we put service that we don't want to be duplicated on
        worker subprocesses
        """
        if self.options.get('global_cache') and self.options.get('cache'):
            # only add the cache service here if the global_cache and cache
            # options were set to True
            _cache = self.getCacheService()
            _cache.startService()
