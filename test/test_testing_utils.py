import pytest

from hendrix.experience import crosstown_traffic
from hendrix.utils.test_utils import AsyncTestMixin, crosstownTaskListDecoratorFactory


def test_assert_num_tasks():
    a_mixin = AsyncTestMixin()
    a_mixin.sub_setUp()
    a_mixin.assertNumCrosstownTasks(0)

    def some_task():
        pass

    through_to_you = crosstown_traffic()
    through_to_you(some_task)

    a_mixin.assertNumCrosstownTasks(1)


def test_next_task():
    a_mixin = AsyncTestMixin()
    a_mixin.sub_setUp()
    a_mixin.assertNumCrosstownTasks(0)

    def some_task():
        pass

    through_to_you = crosstown_traffic()
    through_to_you(some_task)

    assert some_task is a_mixin.next_task()


def test_no_more_tasks():
    a_mixin = AsyncTestMixin()
    a_mixin.sub_setUp()
    a_mixin.assertNumCrosstownTasks(0)

    def some_task():
        pass

    through_to_you = crosstown_traffic()
    through_to_you(some_task)

    same_task = a_mixin.next_task()

    # That will be the only (and thus last) task.
    with pytest.raises(StopIteration):
        a_mixin.next_task()


def test_record_task_to_list():
    task_list = []
    crosstown_traffic.decorator = crosstownTaskListDecoratorFactory(task_list)

    assert len(task_list) == 0

    @crosstown_traffic()
    def add_to_task_list():
        pass

    assert len(task_list) == 1
