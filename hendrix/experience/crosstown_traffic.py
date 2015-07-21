import sys


class ModuleCaller(object):

    def __init__(self, decorator=None):
        if not decorator:
            from hendrix.mechanics.async.decorators import ThroughToYou
            self.decorator = ThroughToYou
        else:
            self.decorator = decorator

        super(ModuleCaller, self).__init__()

    def __call__(self, *args, **kwargs):
        return self.decorator(*args, **kwargs)

sys.modules[__name__] = ModuleCaller()
