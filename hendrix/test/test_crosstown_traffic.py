import threading
from Queue import Queue

from twisted.internet.threads import deferToThreadPool
from twisted.trial.unittest import TestCase
from twisted.internet import reactor
from twisted.internet.defer import gatherResults
from twisted.python.threadpool import ThreadPool
from twisted.web.test.requesthelper import DummyRequest

from twisted.logger import Logger
from hendrix.experience import crosstown_traffic
from hendrix.mechanics.async.exceptions import ThreadHasNoResponse
from hendrix.facilities.resources import HendrixWSGIResource
from hendrix.test.resources import TestNameSpace, application as wsgi_application,\
    nameSpace


log = Logger()


class NoGoStatusCodes(TestCase):

    def __init__(self, *args, **kwargs):
        self.tp = ThreadPool(maxthreads=20)
        self.tp.start()

        self.resource = HendrixWSGIResource(reactor,
                                            self.tp,
                                            self.wsgi_thing)

        self.nameSpace = TestNameSpace()
        self.nameSpace.async_thing_complete = Queue()
        return super(NoGoStatusCodes, self).__init__(*args, **kwargs)

    def setUp(self, *args, **kwargs):
        self.addCleanup(self.tp.stop)
        super(NoGoStatusCodes, self).setUp(*args, **kwargs)

    def wsgi_thing(self, environ, start_response):
            start_response('404 NOT FOUND', [('Content-type','text/plain')])

            @crosstown_traffic(
                no_go_status_codes=self.no_go_status_codes,
                same_thread=True
            )
            def long_thing_on_same_thread():
                self.nameSpace.async_task_was_run = True
                log.debug("No bad status codes; went ahead with async thing.")

            return "Nothing."

    def test_bad_status_codes_cause_no_go_in_wsgi_response(self):
        self.no_go_status_codes = [404, '6xx']

        request = DummyRequest('r1')
        request.isSecure = lambda: False
        request.content = "llamas"

        finished = request.notifyFinish()

        self.resource.render(request)

        # This must wait until the WSGI response is closed.
        finished.addCallback(
            lambda _: self.assertFalse(
                self.nameSpace.async_task_was_run
            )
        )

    def test_bad_status_codes_cause_no_go_flag(self):
        through_to_you = crosstown_traffic(
            no_go_status_codes=[418]
        )
        through_to_you.status_code = 418
        through_to_you.check_status_code_against_no_go_list()
        self.assertTrue(through_to_you.no_go)

    def test_no_bad_status_codes_are_cool(self):
        through_to_you = crosstown_traffic(
            no_go_status_codes=[418]
        )
        through_to_you.status_code = 404
        through_to_you.check_status_code_against_no_go_list()
        self.assertFalse(through_to_you.no_go)


class SameOrDifferentThread(TestCase):

    def setUp(self, *args, **kwargs):
        self.tp = ThreadPool(maxthreads=20)
        self.tp.start()
        self.addCleanup(self.tp.stop)
        super(SameOrDifferentThread, self).setUp(*args, **kwargs)

    def wsgi_thing(self, environ, start_response):
            start_response('200 OK', [('Content-type', 'text/plain')])

            nameSpace.this_thread = threading.current_thread()

            @crosstown_traffic(
                same_thread=self.use_same_thread
            )
            def long_thing_on_same_thread():
                nameSpace.thread_that_is_supposed_to_be_the_same = threading.current_thread()
                log.debug("Finished async thing on same thread.")

            return "Nothing."

    def assert_that_threads_are_the_same(self):
        self.assertEqual(
            nameSpace.this_thread,
            nameSpace.thread_that_is_supposed_to_be_the_same
        )

    def assert_that_threads_are_different(self):
        self.assertNotEqual(nameSpace.this_thread,
                            nameSpace.thread_that_is_supposed_to_be_different)

    def request_same_or_different_thread_thread(self):

        hr = HendrixWSGIResource(reactor, self.tp, self.wsgi_thing)
        request1 = DummyRequest('r1')
        request1.isSecure = lambda: False
        request1.content = "llamas"
        d = deferToThreadPool(reactor, self.tp, hr.render, request1)
        return d

    def test_that_threads_are_the_same(self):
        self.use_same_thread = True
        d = self.request_same_or_different_thread_thread()
        d.addCallback(lambda _: self.assert_that_threads_are_the_same)
        return d

    def test_that_threads_are_different(self):
        self.use_same_thread = False
        d = self.request_same_or_different_thread_thread()
        d.addCallback(lambda _: self.assert_that_threads_are_different)
        return d


class PostResponseTest(TestCase):
    
    def setUp(self):
        nameSpace = TestNameSpace()

    def tearDown(self):
        try:
            del threading.current_thread().response_object
        except AttributeError:
            pass

    def test_postiive_decorator_coherence(self):
        self.pass_flag = False

        def run_me_to_pass():
            self.pass_flag = True

        class FakeResponse(object):
            crosstown_tasks = []
            status = "200 OK"

        through_to_you = crosstown_traffic(same_thread=True)
        threading.current_thread().response_object = FakeResponse()
        through_to_you(run_me_to_pass)
        # threadpool doesn't matter because same_thread is True.
        through_to_you.run(reactor.threadpool)

        self.assertFalse(through_to_you.no_go)  # If the no_go is False...
        self.assertTrue(self.pass_flag)  # Then run_me_to_pass will have run.

    def test_negative_decorator_coherence(self):

        def append_me_to_pass():
            pass

        class FakeResponse(object):
            crosstown_tasks = []
            status = "418 I'm a teapot.  Seriously."

        threading.current_thread().response_object = FakeResponse()
        through_to_you = crosstown_traffic(same_thread=True)

        through_to_you.no_go = True  # If no_go is True...
        through_to_you(append_me_to_pass)  # and we call it...
        self.assertFalse(through_to_you.response.crosstown_tasks)  # We won't have added any tasks.

        through_to_you.no_go = False  # However if no_go is False...
        through_to_you(append_me_to_pass)  # and we call it...
        self.assertEqual(through_to_you.response.crosstown_tasks[0].crosstown_task,
                         append_me_to_pass
                         )  # We will have added the function.

    def test_with_no_request(self):

        self.has_run = False

        def append_me_to_pass():
            self.has_run = True

        through_to_you = crosstown_traffic(same_thread=True)
        through_to_you(append_me_to_pass)

        self.assertTrue(self.has_run)

    def test_fail_without_response(self):
        '''
        Same test as above, but with fail_without_response, we get an error.
        '''
        self.has_run = False

        def append_me_to_pass():
            self.has_run = True

        through_to_you = crosstown_traffic(same_thread=True, fail_without_response=True)

        self.assertRaises(ThreadHasNoResponse, through_to_you, append_me_to_pass)

    def test_contemporaneous_requests(self):

        '''
        We're going to create two request-response cycles here:

        Cycle 1 will begin.
        Cycle 2 will begin.
        Cycle 2 will return.
        Cycle 1 will return.

        This way, we can prove that the crosstown_traffic created
        by cycle 1 is not resolved by the return of cycle 2.
        '''
        tp = ThreadPool(maxthreads=20)
        tp.start()
        self.addCleanup(tp.stop)


        log.debug("\n\nStarting the two stream stuff.")

        request1 = DummyRequest('r1')
        request1.isSecure = lambda: False
        request1.content = "Nothing really here."
        request1.headers['llamas'] = 'dingo'

        nameSpace.test_case = self

        hr = HendrixWSGIResource(reactor, tp, wsgi_application)
        d1 = deferToThreadPool(reactor, tp, hr.render, request1)

        request2 = DummyRequest('r2')
        request2.isSecure = lambda: False
        request2.content = "Nothing really here."
        request2.headers['llamas'] = 'dingo'

        d2 = deferToThreadPool(reactor, tp, hr.render, request2)

        def woah_stop(failure):
            nameSpace.async_task_was_done.put_nowait(False)
            nameSpace.second_cycle_complete.put_nowait(False)
            nameSpace.ready_to_proceed_with_second_cycle.put_nowait(False)

        d1.addErrback(woah_stop)
        d2.addErrback(woah_stop)

        combo_deferred = gatherResults([d1, d2])

        def wait_for_queue_resolution():
            nameSpace.async_task_was_done.get(True, 3)

        combo_deferred.addCallback(
            lambda _: deferToThreadPool(reactor, tp, wait_for_queue_resolution)
        )

        combo_deferred.addCallback(
            lambda _: self.assertTrue(nameSpace.async_task_was_run)
        )

        return combo_deferred
