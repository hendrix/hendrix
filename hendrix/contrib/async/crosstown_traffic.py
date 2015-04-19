from twisted.internet.threads import deferToThread, deferToThreadPool
from twisted.internet import reactor

import threading

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_response_for_thread(thread=None):

    if not thread:
        thread = threading.current_thread()

    response = thread.response_object
    return response


def get_tasks_to_follow_current_response(thread=None):
    response = get_response_for_thread(thread)
    return response.crosstown_tasks


class ThroughToYou(object):

    def __init__(self,
                 same_thread=False,
                 no_go_status_codes=['5xx', '4xx'],
                 reactor=reactor,
                 ):
        self.same_thread = same_thread
        self.no_go_status_codes = no_go_status_codes
        self.reactor = reactor
        self.no_go = False
        self.status_code = None

    def __call__(self, crosstown_task):
        self.crosstown_task = crosstown_task
        self.response = get_response_for_thread()

        if not self.no_go:
            logger.info("Adding '%s' to crosstown_traffic for %s" % (crosstown_task.__name__, self.response))
            self.response.crosstown_tasks.append(self)

    def run(self, threadpool):
        # See if status code is a go
        self.check_status_code_against_no_go_list()
        if self.no_go:
            return

        if self.same_thread:
            self.crosstown_task()
        else:
            deferToThreadPool(reactor, threadpool, self.crosstown_task)

    def populate_no_go_status_code_list(self):
        self.no_go_status_code_list = []

        for no_go_code in self.no_go_status_codes:
            if type(no_go_code) == str:
                if "xx" in no_go_code:
                    class_number = int(no_go_code[0])
                    begin = class_number * 100
                    end = begin + 100
                elif '-' in no_go_code:
                    begin, end = no_go_code.split('-')
                else:
                    self.no_go_status_code_list.extend(int(no_go_code))
                    continue
                self.no_go_status_code_list.extend(range(begin, end))

            else:
                 self.no_go_status_code_list.append(no_go_code)

        logger.debug("no_go_status_codes are %s" % self.no_go_status_code_list)

    def check_status_code_against_no_go_list(self):
        if self.no_go_status_codes:
            if not self.status_code:
                self.status_code = int(self.response.status.split(None, 1)[0])

            self.populate_no_go_status_code_list()

            if self.status_code in self.no_go_status_code_list:
                logger.info("Flagging no-go becasue status code is %s" % self.status_code)
                self.no_go = True


class FollowResponse(object):

    def __call__(self, *args, **kwargs):
        decorator = ThroughToYou(*args, **kwargs)
        return decorator

follow_response = FollowResponse()
