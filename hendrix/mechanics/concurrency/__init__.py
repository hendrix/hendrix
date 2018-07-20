import threading

from hendrix.mechanics.concurrency.exceptions import ThreadHasNoResponse


def get_response_for_thread(thread=None):
    if not thread:
        thread = threading.current_thread()

    try:
        response = thread.response_object
    except AttributeError:
        raise ThreadHasNoResponse('thread %s has no associated response object.' % thread)

    return response


def get_tasks_to_follow_current_response(thread=None):
    response = get_response_for_thread(thread)
    return response.crosstown_tasks
