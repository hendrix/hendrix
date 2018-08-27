import threading

from twisted.internet import reactor
from twisted.logger import Logger
from twisted.web.wsgi import _WSGIResponse

from hendrix.utils import responseInColor


class HendrixWSGIResponse(_WSGIResponse):
    log = Logger()

    def __init__(self, *args, **kwargs):
        self.crosstown_tasks = []
        return super(HendrixWSGIResponse, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        r = reactor
        self.thread = threading.current_thread()
        # thread_list.append(self.thread)  # Debug
        # logger.debug("Assigning %s as the current response for thread %s" % (self, self.thread))
        self.thread.response_object = self
        self.request.setHeader('server', 'hendrix/Twisted')
        ran = super(HendrixWSGIResponse, self).run(*args, **kwargs)
        self.follow_response_tasks()
        del self.thread.response_object
        return ran

    def follow_response_tasks(self):
        for task in self.crosstown_tasks:
            self.log.info("Processing crosstown task: '%s'" % task.crosstown_task)

            # Set no-go if status code is bad.
            task.check_status_code_against_no_go_list()

            task.run()


class LoudWSGIResponse(HendrixWSGIResponse):

    def startResponse(self, status, headers, excInfo=None):
        """
        extends startResponse to call speakerBox in a thread
        """
        self.status = status
        self.headers = headers
        self.reactor.callInThread(
            responseInColor, self.request, status, headers
        )
        return self.write
