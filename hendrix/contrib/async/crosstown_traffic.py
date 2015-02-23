from twisted.internet.threads import deferToThread
from twisted.test.proto_helpers import MemoryReactor


# TODO: Figure out how to follow *this* response, not just any response.
task_to_follow_response = []


def follow_response():
    '''
    Run the function immediately after the WSGIResponse is run.
    '''
    def decorator(f):
        task_to_follow_response.append(f)
    return decorator