from multiprocessing import Queue

from twisted.logger import Logger

from hendrix.experience import crosstown_traffic
from hendrix.mechanics.concurrency import get_response_for_thread, get_tasks_to_follow_current_response

log = Logger()


class TestNameSpace(object):
    async_task_was_done = Queue()
    async_task_was_run = False
    ready_to_proceed_with_second_cycle = Queue()
    second_cycle_complete = Queue()


nameSpace = TestNameSpace()


def application(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/plain')])

    if 'test_crosstown_traffic' in environ['QUERY_STRING'] or environ['PATH_INFO'] == '/r1':
        log.debug('Starting first cycle...')

        @crosstown_traffic()
        def delayed_callable():
            TestNameSpace.async_task_was_run = True

            # This is the end of the test logic.
            TestNameSpace.async_task_was_done.put(None)

        # Save this response as the "first response" so that we can check later
        nameSpace.first_response = get_response_for_thread()

        tasks = nameSpace.first_response.crosstown_tasks

        # We have one task to run after the response.
        assert len(tasks) == 1

        # The async task flag is still false (ie, the task hasn't run.)
        assert not nameSpace.async_task_was_run

        # Clear second cycle to begin.
        nameSpace.ready_to_proceed_with_second_cycle.put(True)

        # OK!  Hold here until the second cycle completes.
        nameSpace.second_cycle_complete.get(True, 3)

        # Second cycle has completed, yet it didn't steal our crosstown_traffic
        assert len(tasks) == 1

        # ...and again, the async task still hasn't been run yet.
        assert not nameSpace.async_task_was_run

        return [b'The first sync response']

    if environ['PATH_INFO'] == '/r2':
        nameSpace.ready_to_proceed_with_second_cycle.get(True, 3)

        second_response_tasks = get_tasks_to_follow_current_response()

        # We didn't set any tasks during the second response.
        assert not second_response_tasks

        # However, the single task assigned during the first response is still
        # milling about.
        first_response_tasks = nameSpace.first_response.crosstown_tasks

        # And The async task flag is *still* false (ie, the task still has not
        # run, but it will once the first request finishes.)
        assert not nameSpace.async_task_was_run

        assert len(first_response_tasks) == 1

        # ...and it's the one defined above.
        assert first_response_tasks[0].crosstown_task.__name__ == 'delayed_callable'

        nameSpace.second_cycle_complete.put(True)
        return [b'The second sync request.']

    other_inane_thing = False

    return [b"Finished."]
