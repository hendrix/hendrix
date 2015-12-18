import sys
from twisted.python.threadpool import ThreadPool
from twisted.internet import reactor


class ModuleCaller(object):

    decorator = None

    def __init__(self, decorator=None):
        from hendrix.mechanics.async.decorators import ThroughToYou
        self.decorator = decorator or self.decorator or ThroughToYou
        self.threadpool = ThreadPool(name="Crosstown Traffic")

	# The threadpool needs to start when the reactors starts...
        reactor.callWhenRunning(self.threadpool.start)
	# ...and stop when the reactor stops.
        reactor.addSystemEventTrigger('before', 'shutdown', self.threadpool.stop)


        super(ModuleCaller, self).__init__()

    def __call__(self, *args, **kwargs):
        try:
            return self.decorator(threadpool=self.threadpool, *args, **kwargs)
        except TypeError as e:
            if e.args[0] == "__init__() got multiple values for keyword argument 'threadpool'":
                raise TypeError("Did you forget the '()' when using the crosstown_traffic decorator?  (ie, '@crosstown_traffic()').  Caught '%s'" % e.args[0])
            else:
                raise


sys.modules[__name__] = ModuleCaller()
