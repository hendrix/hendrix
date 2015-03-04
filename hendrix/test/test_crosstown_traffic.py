from unittest.case import TestCase

from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from twisted.python.threadpool import ThreadPool
from twisted.web.client import Agent
from twisted.web.test.requesthelper import DummyRequest

from hendrix.contrib.async import crosstown_traffic
from hendrix.resources import HendrixWSGIResource
from hendrix.test.resources import TestNameSpace, application as wsgi_application,\
    nameSpace
from functools import partial
from time import sleep



import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)
logger = logging.getLogger(__name__)



def fakeCallFromThread(func, *args, **kw):
    return func(*args, **kw)

def fakeCallInThreadWithCallback(onResult, func, *args, **kw):
    return func(*args, **kw)
    

tp = ThreadPool(1)
tp.callInThreadWithCallback = fakeCallInThreadWithCallback


class PostResponseTest(TestCase):
    
    def setUp(self):
        nameSpace = TestNameSpace()
    
    def test_contemporaneous_requests(self):
        
        r = reactor

        def cross_threads():
            '''
            We're going to create two request-response cycles here:
            
            Cycle 1 will begin.
            Cycle 2 will begin.
            Cycle 2 will return.
            Cycle 1 will return.
            
            This way, we can prove that the crosstown_traffic created
            by cycle 1 is not resolved by the return of cycle 2.
            '''
            logger.info("\n\nReactor started; calling cross_threads.")
            
            request1 = DummyRequest('r1')
            request1.isSecure = lambda: False
            request1.content = "Nothing really here."
            request1.headers['llamas'] = 'dingo'

            nameSpace.test_case = self

            hr = HendrixWSGIResource(reactor, tp, wsgi_application)
            r.callInThread(hr.render, request1)
     
            request2 = DummyRequest('r2')
            request2.isSecure = lambda: False
            request2.content = "Nothing really here."
            request2.headers['llamas'] = 'dingo'
                
            r.callInThread(hr.render, request2)
        
        r.callWhenRunning(cross_threads)

        r.run()
        
        # Only now has the async task finally run.
        self.assertTrue(nameSpace.async_task_was_run)