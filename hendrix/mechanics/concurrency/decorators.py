import threading

from twisted.internet import reactor
from twisted.internet.threads import deferToThreadPool
from twisted.logger import Logger

from hendrix.mechanics.concurrency import get_response_for_thread
from hendrix.mechanics.concurrency.exceptions import ThreadHasNoResponse


class _ThroughToYou(object):
    log = Logger()

    def __init__(self,
                 threadpool=None,
                 reactor=reactor,
                 same_thread=False,
                 no_go_status_codes=['5xx', '4xx'],
                 fail_without_response=False,
                 block_without_response=True,
                 always_spawn_worker=False,
                 ):
        self.threadpool = threadpool
        self.reactor = reactor
        self.same_thread = same_thread
        self.no_go_status_codes = no_go_status_codes or ['5xx', '4xx']
        self.fail_without_response = fail_without_response
        self.block_without_response = block_without_response
        self.always_spawn_worker = always_spawn_worker

        self.no_go = False
        self.status_code = None
        self.crosstown_task = None

    def __call__(self, crosstown_task=None):
        self.crosstown_task = crosstown_task

        try:
            self.response = get_response_for_thread()
            self.log.info("Adding '%s' to crosstown_traffic for %s" % (str(crosstown_task), self.response))
            if not self.no_go:
                self.response.crosstown_tasks.append(self)
        except ThreadHasNoResponse:
            self.responseless_fallback(crosstown_task)
        return self.run

    def responseless_fallback(self, crosstown_task=None):
        self.crosstown_task = crosstown_task or self.crosstown_task

        if self.fail_without_response:
            raise ThreadHasNoResponse(
                "This crosstown decorator cannot proceed without a response.  To run the crosstown_task at this time, set fail_without_response = False.")
        else:
            self.log.info(
                "thread %s has no response; running crosstown task now.  To supress this behavior, set fail_without_response == True." % threading.current_thread())
            # Since we have no response, we now want to run on the same thread if block_without_response is True.
            self.same_thread = self.block_without_response
            self.run()

    def run(self, threadpool=None):
        if self.no_go:
            return
        if self.same_thread:
            self.crosstown_task()
        else:
            if not threadpool:
                threadpool = self.threadpool or reactor.getThreadPool()
            if self.always_spawn_worker:
                threadpool.startAWorker()

            deferToThreadPool(reactor, threadpool, self.crosstown_task)

            # if self.always_spawn_worker:
            #     threadpool.stopAWorker()

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

        self.log.debug("no_go_status_codes are %s" % self.no_go_status_code_list)

    def check_status_code_against_no_go_list(self):
        if self.no_go_status_codes:
            if not self.status_code:
                self.status_code = int(self.response.status.split(None, 1)[0])

            self.populate_no_go_status_code_list()

            if self.status_code in self.no_go_status_code_list:
                self.log.info("Flagging no-go becasue status code is %s" % self.status_code)
                self.no_go = True
