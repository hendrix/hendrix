from twisted.internet.threads import deferToThread, deferToThreadPool
from twisted.internet import reactor
from twisted.python.threadpool import ThreadPool

import threading

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ThreadHasNoResponse(RuntimeError):
    pass


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


class ThroughToYou(object):

    def __init__(self,
                 reactor=reactor,
                 same_thread=False,
                 no_go_status_codes=['5xx', '4xx'],
                 fail_without_response=False
                 ):
        self.reactor = reactor
        self.same_thread = same_thread
        self.no_go_status_codes = no_go_status_codes
        self.fail_without_response = fail_without_response

        self.no_go = False
        self.status_code = None

    def __call__(self, crosstown_task=None):
        self.crosstown_task = crosstown_task

        try:
            self.response = get_response_for_thread()
            logger.info("Adding '%s' to crosstown_traffic for %s" % (str(crosstown_task), self.response))
            if not self.no_go:
                self.response.crosstown_tasks.append(self)
        except ThreadHasNoResponse:
            if self.fail_without_response:
                raise
            else:
                logger.info("thread %s has no response; running crosstown task now.  To supress this behavior, set fail_without_response == True." % threading.current_thread())
                self.run()
        return self.run

    def run(self, threadpool=None):
        if self.no_go:
            return

        if not threadpool:
            threadpool = reactor.threadpool or ThreadPool()

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
