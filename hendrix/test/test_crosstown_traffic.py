from unittest.case import TestCase
from twisted.test.proto_helpers import MemoryReactor
from hendrix.resources import HendrixWSGIResource
from twisted.python.threadpool import ThreadPool
from twisted.web.test.requesthelper import DummyRequest
from hendrix.contrib.async import crosstown_traffic

def fakeCallFromThread(func, *args, **kw):
    return func(*args, **kw)

def fakeCallInThreadWithCallback(onResult, func, *args, **kw):
    return func(*args, **kw)
    

tp = ThreadPool(1)
tp.callInThreadWithCallback = fakeCallInThreadWithCallback

reactor = MemoryReactor()
reactor.callFromThread = fakeCallFromThread


class TestNameSpace(object):
    async_task_was_run = False


class PostResponseTest(TestCase):
       
    def test_llamas(self):
        
        def application(environ, start_response):
            start_response('200 OK', [('Content-type','text/plain')])
        
            @crosstown_traffic.follow_response()
            def finish_thing():
                TestNameSpace.async_task_was_run = True
        
            return ['The synchronous response']

        hr = HendrixWSGIResource(reactor, tp, application)
        request = DummyRequest('/nowhere/')
        request.isSecure = lambda: False
        request.content = "Nothing really here."
        
        # Async thing hasn't yet occured.
        self.assertFalse(TestNameSpace.async_task_was_run)        
        
        # but now...
        response = hr.render(request)
        
        # It has.
        self.assertTrue(TestNameSpace.async_task_was_run)