import sys

from twisted.internet import reactor
from twisted.python.threadpool import ThreadPool


class ModuleCaller(object):
    decorator = None

    def __init__(self, decorator=None):
        from hendrix.mechanics.concurrency.decorators import _ThroughToYou
        self.decorator = decorator or self.decorator or _ThroughToYou
        self.threadpool = ThreadPool(name="Crosstown Traffic")

        # The threadpool needs to start when the reactors starts...
        reactor.callWhenRunning(self.threadpool.start)
        # ...and stop when the reactor stops.
        reactor.addSystemEventTrigger('before', 'shutdown', self.threadpool.stop)

        super(ModuleCaller, self).__init__()

    def __call__(self, *args, **kwargs):
        try:
            threadpool = kwargs.pop('threadpool', self.threadpool)
            return self.decorator(threadpool=threadpool, *args, **kwargs)
        except TypeError as e:
            if e.args[0] == "__init__() got multiple values for keyword argument 'threadpool'":
                raise TypeError(
                    "Did you forget the '()' when using the crosstown_traffic decorator?  (ie, '@crosstown_traffic()').  Caught '%s'" %
                    e.args[0])
            else:
                raise


sys.modules[__name__] = ModuleCaller()
