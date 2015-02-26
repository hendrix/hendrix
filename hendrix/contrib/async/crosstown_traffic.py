from twisted.internet.threads import deferToThread
from twisted.internet import reactor

import threading

# TODO: Figure out how to follow *this* response, not just any response.
task_to_follow_response = []


def follow_response():
    '''
    Run the function immediately after the WSGIResponse is run.
    '''
    def decorator(f):
        print threading.current_thread().response_object  # Proves that we have acces to the response object
        r = reactor
        task_to_follow_response.append(f)
    return decorator