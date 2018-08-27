from hendrix.experience import crosstown_traffic
from hendrix.mechanics.concurrency.decorators import _ThroughToYou


def crosstownTaskListDecoratorFactory(list_to_populate):
    class TaskListThroughToYou(_ThroughToYou):

        def __init__(self, *args, **kwargs):
            self.crosstown_task_list = list_to_populate
            super(TaskListThroughToYou, self).__init__(*args, **kwargs)

        def responseless_fallback(self, crosstown_task):
            self.crosstown_task_list.append(crosstown_task)

    return TaskListThroughToYou


class AsyncTestMixin(object):

    def setUp(self):
        self.sub_setUp()
        return super(AsyncTestMixin, self).setUp()

    def sub_setUp(self):
        self.recorded_tasks = []
        crosstown_traffic.decorator = crosstownTaskListDecoratorFactory(self.recorded_tasks)
        crosstown_traffic()
        self.archived_tasks = []

    def next_task(self):
        for task in self.recorded_tasks:
            if task not in self.archived_tasks:
                self.archived_tasks.append(task)
                return task

        raise StopIteration("No more tasks.")

    def assertNumCrosstownTasks(self, num_tasks):
        if not num_tasks == len(self.recorded_tasks):
            raise AssertionError(
                "There were not %s recorded tasks.  The recorded tasks were: %s" % (num_tasks, self.recorded_tasks))
