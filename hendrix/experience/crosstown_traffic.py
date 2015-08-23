import sys
from twisted.python.threadpool import ThreadPool


class ModuleCaller(object):

    decorator = None

    def __init__(self, decorator=None):
        from hendrix.mechanics.async.decorators import ThroughToYou
        self.decorator = decorator or self.decorator or ThroughToYou
        self.threadpool = ThreadPool(name="Crosstown Traffic")
        self.threadpool.start()

        super(ModuleCaller, self).__init__()

    def __call__(self, *args, **kwargs):
        return self.decorator(threadpool=self.threadpool, *args, **kwargs)

sys.modules[__name__] = ModuleCaller()
