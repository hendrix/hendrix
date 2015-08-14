from hendrix.experience import crosstown_traffic
from hendrix.utils.test_utils import AsyncTestMixin, crosstownTaskListDecoratorFactory
from twisted.trial.unittest import TestCase


class TestMixinAssertions(TestCase):

    def test_assert_num_tasks(self):

        a_mixin = AsyncTestMixin()
        a_mixin.sub_setUp()
        a_mixin.assertNumCrosstownTasks(0)

        def some_task():
            pass

        through_to_you = crosstown_traffic()
        through_to_you(some_task)

        a_mixin.assertNumCrosstownTasks(1)

    def test_next_task(self):

        a_mixin = AsyncTestMixin()
        a_mixin.sub_setUp()
        a_mixin.assertNumCrosstownTasks(0)

        def some_task():
            pass

        through_to_you = crosstown_traffic()
        through_to_you(some_task)

        self.assertIs(some_task, a_mixin.next_task())

    def test_no_more_tasks(self):

        a_mixin = AsyncTestMixin()
        a_mixin.sub_setUp()
        a_mixin.assertNumCrosstownTasks(0)

        def some_task():
            pass

        through_to_you = crosstown_traffic()
        through_to_you(some_task)

        same_task = a_mixin.next_task()

        # That will be the only (and thus last) task.
        self.assertRaises(StopIteration, a_mixin.next_task)


class TestRecordTasksAsList(TestCase):

    def test_record_task_to_list(self):
        task_list = []
        crosstown_traffic.decorator = crosstownTaskListDecoratorFactory(task_list)

        self.assertEqual(len(task_list), 0)

        @crosstown_traffic()
        def add_to_task_list():
            print "this will be in the task list"

        self.assertEqual(len(task_list), 1)