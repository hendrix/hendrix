import threading

import pytest
import pytest_twisted
from six.moves.queue import Queue
from twisted.internet import reactor
from twisted.internet.address import IPv4Address
from twisted.internet.threads import deferToThreadPool
from twisted.logger import Logger
from twisted.python.threadpool import ThreadPool
from twisted.trial.unittest import TestCase
from twisted.web.test.requesthelper import DummyRequest

from hendrix.experience import crosstown_traffic
from hendrix.facilities.resources import HendrixWSGIResource
from hendrix.mechanics.concurrency.exceptions import ThreadHasNoResponse
from test.resources import TestNameSpace, application as wsgi_application, \
    nameSpace

log = Logger()

# Using module-scoped list to keep track of pass flags.  When we drop support for Python 2, we can use nonlocal instead.
pass_flags = []


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
        start_response('404 NOT FOUND', [('Content-type', 'text/plain')])

        @crosstown_traffic(
            no_go_status_codes=self.no_go_status_codes,
            same_thread=True
        )
        def long_thing_on_same_thread():
            self.nameSpace.async_task_was_run = True
            log.debug("No bad status codes; went ahead with async thing.")

        return [b"Nothing."]

    def test_bad_status_codes_cause_no_go_in_wsgi_response(self):
        self.no_go_status_codes = [404, '6xx']

        request = DummyRequest([b'r1'])
        request.isSecure = lambda: False
        request.content = "llamas"
        request.client = IPv4Address("TCP", b"50.0.50.0", 5000)

        finished = request.notifyFinish()

        self.resource.render(request)

        # This must wait until the WSGI response is closed.
        finished.addCallback(
            lambda _: self.assertFalse(
                self.nameSpace.async_task_was_run
            )
        )

        return finished

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
        self.tp = ThreadPool()
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

        return [b"Nothing."]

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
        request1 = DummyRequest([b'r1'])
        request1.isSecure = lambda: False
        request1.content = b"llamas"
        request1.client = IPv4Address("TCP", b"50.0.50.0", 5000)
        d = deferToThreadPool(reactor, self.tp, hr.render, request1)
        d.addCallback(lambda _: request1.notifyFinish())
        return d

    def test_that_threads_are_the_same(self):
        self.use_same_thread = True
        d = self.request_same_or_different_thread_thread()
        d.addCallback(lambda _: self.assert_that_threads_are_the_same)
        return pytest_twisted.blockon(d)

    def test_that_threads_are_different(self):
        self.use_same_thread = False
        d = self.request_same_or_different_thread_thread()
        d.addCallback(lambda _: self.assert_that_threads_are_different)
        return pytest_twisted.blockon(d)


@pytest.fixture
def async_namespace():
    nameSpace = TestNameSpace()
    yield
    try:
        del threading.current_thread().response_object
    except AttributeError:
        pass


@pytest.mark.usefixtures("async_namespace")
def test_typical_same_thread_operation():
    success_string = "With a Response affixed to this thread, the task will run if the status code is not a 'no-go'."

    def run_me_to_pass():
        pass_flags.append(success_string)

    class FakeResponse(object):
        crosstown_tasks = []
        status = "200 OK"

    through_to_you = crosstown_traffic(same_thread=True)
    threading.current_thread().response_object = FakeResponse()
    through_to_you(run_me_to_pass)
    # threadpool doesn't matter because same_thread is True.

    # The function hasn't run yet.
    assert success_string not in pass_flags
    through_to_you.run(reactor.threadpool)

    assert not through_to_you.no_go  # Since the no_go is False...
    assert success_string in pass_flags  # Then run_me_to_pass will have run.


@pytest.mark.usefixtures("async_namespace")
def test_no_go_causes_task_not_to_fire():
    some_task = lambda: None

    class FakeResponse(object):
        crosstown_tasks = []
        status = "418 I'm a teapot.  Seriously."

    threading.current_thread().response_object = FakeResponse()
    through_to_you = crosstown_traffic(same_thread=True)

    through_to_you.no_go = True  # If no_go is True...
    through_to_you(some_task)  # and we call it...
    assert not through_to_you.response.crosstown_tasks  # We won't have added any tasks.

    through_to_you.no_go = False  # However if no_go is False...
    through_to_you(some_task)  # and we call it...

    # We will have added the function.
    assert through_to_you.response.crosstown_tasks[0].crosstown_task == some_task


@pytest.mark.usefixtures("async_namespace")
def test_with_no_request():
    success_string = "Without a request in progress, the default behavior for crosstown_traffic is to run the task immediately."

    def append_me_to_pass():
        pass_flags.append(success_string)

    through_to_you = crosstown_traffic(same_thread=True)

    assert success_string not in pass_flags
    through_to_you(append_me_to_pass)
    assert success_string in pass_flags


@pytest.mark.usefixtures("async_namespace")
def test_fail_without_response():
    '''
    Same test as above, but with fail_without_response, we get an error.
    '''
    some_task = lambda: None

    through_to_you = crosstown_traffic(same_thread=True, fail_without_response=True)

    with pytest.raises(ThreadHasNoResponse):
        through_to_you(some_task)


@pytest.mark.usefixtures("async_namespace")
@pytest_twisted.inlineCallbacks
def test_contemporaneous_requests():
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

    log.debug("\n\nStarting the two stream stuff.")

    request1 = DummyRequest([b'r1'])
    request1.isSecure = lambda: False
    request1.content = "Nothing really here."
    request1.requestHeaders.addRawHeader('llamas', 'dingo')
    request1.client = IPv4Address("TCP", b"50.0.50.0", 5000)

    hr = HendrixWSGIResource(reactor, tp, wsgi_application)
    yield deferToThreadPool(reactor, tp, hr.render, request1)

    request2 = DummyRequest([b'r2'])
    request2.isSecure = lambda: False
    request2.content = b"Nothing really here."
    request2.requestHeaders.addRawHeader('llamas', 'dingo')
    request2.client = IPv4Address("TCP", b"100.0.50.0", 5000)

    yield deferToThreadPool(reactor, tp, hr.render, request2)

    # def woah_stop(failure):
    #     nameSpace.async_task_was_done.put_nowait(False)
    #     nameSpace.second_cycle_complete.put_nowait(False)
    #     nameSpace.ready_to_proceed_with_second_cycle.put_nowait(False)
    #
    # d1.addErrback(woah_stop)
    # d2.addErrback(woah_stop)

    # combo_deferred = gatherResults([d1, d2])
    # yield d1
    # yield d2
    # combo_deferred = DeferredList([d1, d2])

    def wait_for_queue_resolution():
        nameSpace.async_task_was_done.get(True, 3)

    # combo_deferred.addCallback(
    #     lambda _:
    # )
    #
    yield deferToThreadPool(reactor, tp, wait_for_queue_resolution)

    # combo_deferred.addCallback(
    #     lambda _:
    # )
    assert nameSpace.async_task_was_run
    tp.stop()

    # return pytest_twisted.blockon(combo_deferred)
