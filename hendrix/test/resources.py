from multiprocessing import Queue
import threading
import logging

from hendrix.contrib.async import crosstown_traffic

logger = logging.getLogger(__name__)


from hendrix.contrib.async.crosstown_traffic import get_response_for_thread,\
    get_tasks_to_follow_current_response


class TestNameSpace(object):

    async_task_was_done = Queue()
    async_task_was_run = False
    ready_to_proceed_with_second_cycle = Queue()
    second_cycle_complete = Queue()
    
nameSpace = TestNameSpace()


def application(environ, start_response):
    start_response('200 OK', [('Content-type','text/plain')])
    
    if 'test_crosstown_traffic' in environ['QUERY_STRING'] or environ['PATH_INFO'] == '/r/1':
        logger.info("Starting first cycle.")
        
        @crosstown_traffic.follow_response()
        def delayed_callable():
            logger.info("Running async logic called by first cycle.")
            TestNameSpace.async_task_was_run = True

            # This is the end of the test logic.
            TestNameSpace.async_task_was_done.put(None)

        # Save this response as the "first response" so that we can check later.
        nameSpace.first_response = get_response_for_thread()
            
        tasks = nameSpace.first_response.crosstown_tasks
        
        logger.info("Making first cycle assertions.")
        
        # We have one task to run after the response.
        nameSpace.test_case.assertEqual(len(tasks), 1)
        
        # The async task flag is still false (ie, the task hasn't run.)
        nameSpace.test_case.assertFalse(nameSpace.async_task_was_run)

        # Clear second cycle to begin.
        logger.info("Clearing second cycle to begin.")
        nameSpace.ready_to_proceed_with_second_cycle.put(True)
        
        # OK!  Hold here until the second cycle completes.
        logger.info('First cycle is paused, waiting for second cycle to complete before returning.')
        nameSpace.second_cycle_complete.get(True, 3)

        # Second cycle has completed, yet it didn't steal our crosstown_traffic.
        nameSpace.test_case.assertEqual(len(tasks), 1)

        # ...and again, the async task still hasn't been run yet.
        nameSpace.test_case.assertFalse(nameSpace.async_task_was_run)
        
        logger.info("First cycle received clearance to unpause; returning first cycle.")
        return ['The first sync response']

    if environ['PATH_INFO'] == '/r/2':
        logger.info("Second cycle waiting to be cleared to start.")
        nameSpace.ready_to_proceed_with_second_cycle.get(True, 3)
        
        logger.info("Starting Second cycle.")

        second_response_tasks = get_tasks_to_follow_current_response()
        
        logger.info("Making second cycle assertions.")
        # We didn't set any tasks during the second response.
        nameSpace.test_case.assertFalse(second_response_tasks)
        
        # However, the single task assigned during the first response is still milling about.
        first_response_tasks = nameSpace.first_response.crosstown_tasks

        # And The async task flag is *still* false (ie, the task still has not run, but it will once the first request finishes.)
        nameSpace.test_case.assertFalse(nameSpace.async_task_was_run)
        
        nameSpace.test_case.assertEqual(len(first_response_tasks), 1)
        
        # ...and it's the one defined above.
        nameSpace.test_case.assertEqual(first_response_tasks[0].crosstown_task.__name__,
                                        'delayed_callable')

        logger.info("Ending second cycle, clearing first cycle to unpause.")
        nameSpace.second_cycle_complete.put(True)
        return['The second sync request.']
        
    other_inane_thing = False

    return [str(threading.current_thread()),
            str(crosstown_traffic.tasks_to_follow_response)]
