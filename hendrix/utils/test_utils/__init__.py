from twisted.logger import Logger
from hendrix.experience import crosstown_traffic
from hendrix.mechanics.async.decorators import ThroughToYou


class MockThroughToYou(ThroughToYou):

    log = Logger()
    warned_strange_overuse = False

    def __call__(self, crosstown_task):
        try:
            crosstown_traffic.recorded_tasks.append(crosstown_task)
        except AttributeError:
            raise TypeError('This is a MockThroughToYou object; it must be used with AsyncTestMixin or another compatible ThroughToYou object.  If this is happening in production, this is a big deal.')

        if len(crosstown_traffic.recorded_tasks) > 10 and not self.warned_strange_overuse:
            self.log.warning("More than 10 tasks have been recorded in a pattern meant for tests.  If this app is in production, something is wrong.")
            self.warned_strange_overuse = True

        super(MockThroughToYou, self).__call__(crosstown_task)


class AsyncTestMixin(object):

    def setUp(self):
        self.sub_setUp()
        return super(AsyncTestMixin, self).setUp()

    def sub_setUp(self):
        crosstown_traffic.decorator = MockThroughToYou
        crosstown_traffic()
        self.archived_tasks = []
        self.recorded_tasks = crosstown_traffic.recorded_tasks = []

    def tearDown(self):
        crosstown_traffic.__call__ = self.old_call
        return super(AsyncTestMixin, self).tearDown()

    def next_task(self):
        for task in self.recorded_tasks:
            if task not in self.archived_tasks:
                self.archived_tasks.append(task)
                return task

        raise StopIteration("No more tasks.")

    def assertNumCrosstownTasks(self, num_tasks):
        if not num_tasks == len(self.recorded_tasks):
            raise AssertionError("There were not %s recorded tasks.  The recorded tasks were: %s" % (num_tasks, self.recorded_tasks))