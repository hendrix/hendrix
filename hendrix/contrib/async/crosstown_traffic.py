from twisted.internet.threads import deferToThread
from twisted.internet import reactor

import threading

import logging

logger = logging.getLogger(__name__)

# TODO: Figure out how to follow *this* response, not just any response.
tasks_to_follow_response = {}

def get_response_for_thread(thread=None):

    if not thread:
        thread = threading.current_thread()

    response = thread.response_object
    return response

def get_tasks_to_follow_response(response):
    return tasks_to_follow_response.get(response, [])

def get_tasks_to_follow_current_response(thread=None):
    response = get_response_for_thread(thread)
    return get_tasks_to_follow_response(response)
    

class ThroughToYou(object):

    def __init__(self,
                 same_thread=False,
                 reactor=reactor,
                 ):
        self.same_thread = same_thread
        self.reactor = reactor

    def __call__(self, crosstown_task):
        self.crosstown_task = crosstown_task
        response = get_response_for_thread()  # Proves that we have access to the response object

        if not tasks_to_follow_response.has_key(response):
            logger.info('Initializing crosstown_traffic for %s' % response)
            tasks_to_follow_response[response] = []

        logger.info("Adding '%s' to crosstown_traffic for %s" % (crosstown_task.__name__, response))
        tasks_to_follow_response[response].append(self)

    def run(self):
        if self.same_thread:
            self.crosstown_task()
        else:
            self.reactor.callInThread(self.crosstown_task)



class FollowResponse(object):

    def __call__(self, *args, **kwargs):
        decorator = ThroughToYou(*args, **kwargs)
        return decorator






#
# def follow_response(*args, **kwargs):
#     '''
#     Run the function immediately after the WSGIResponse is run.
#     '''
#
#     print args, kwargs

follow_response = FollowResponse()
