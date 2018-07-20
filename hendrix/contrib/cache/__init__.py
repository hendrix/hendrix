try:
    import cStringIO
except ImportError:
    from io import BytesIO as cStringIO
import gzip
from datetime import datetime

try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse

from time import strptime
from twisted.web.resource import Resource


def compressBuffer(buffer):
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


def decompressBuffer(buffer):
    "complements the compressBuffer function in CacheClient"
    zbuf = cStringIO.StringIO(buffer)
    zfile = gzip.GzipFile(fileobj=zbuf)
    deflated = zfile.read()
    zfile.close()
    return deflated


class CachedResource(Resource):
    isLeaf = True

    def __init__(self, content=None, headers=None):
        Resource.__init__(self)
        self.content = content
        self.headers = headers
        self.created = datetime.now()

    def render(self, request):
        return self.content

    def getMaxAge(self):
        "get the max-age in seconds from the saved headers data"
        max_age = 0
        cache_control = self.headers.get('cache-control')
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
