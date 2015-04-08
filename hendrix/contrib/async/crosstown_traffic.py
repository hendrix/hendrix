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
    


def follow_response():
    '''
    Run the function immediately after the WSGIResponse is run.
    '''
    def decorator(callable):
        response = get_response_for_thread() # Proves that we have acces to the response object
        r = reactor
        if not tasks_to_follow_response.has_key(response):
            logger.info('Initializing crosstown_traffic for %s' % response)
            tasks_to_follow_response[response] = []
        
        logger.info("Adding '%s' to crosstown_traffic for %s" % (callable.__name__, response))
        tasks_to_follow_response[response].append(callable)
    return decorator