import zlib
from twisted.web.proxy import ReverseProxy


class CacheReverseProxy(ReverseProxy):

    show_me_the_cache = {}  # url: [data, created, max_age, etag?]

    def lineReceived(self, path):
        import ipdb; ipdb.set_trace()

        # check protocol
        # if protocol is secure then pass it on
        #
        # check method
        # if method is POST, PUT or DELETE then pass the request on
        #
        # check freshness
        # if not fresh then validate
        # if fresh then check cached pages
        # if url is not in cached pages then get page, serve and call cache function
        # else serve cached page


    # def lineReceived(self, line):
    #     if not line.startswith("http://"):
    #         return
    #
    #     deferredData = self._getPage(line)
    #     deferredData.addCallback(self.sendAndClose)
    #
    # def _getPage(self, line):
    #     if line in self.factory.caches:
    #         print 'found in cache', line
    #         return defer.succeed(self.factory.caches[line])
    #
    #     print 'fetching', line
    #     d = getPage(line)
    #     d.addCallback(self._storeCache, line)
    #     return d
    #
    # def _storeCache(self, data, line):
    #     print 'fetched', line
    #     self.factory.caches[line] = data
    #     return data
    #
    # def sendAndClose(self, data):
    #     self.transport.write(data)
    #     self.transport.loseConnection()
