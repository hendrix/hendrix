import os
import sys
import threading
import time
from multiprocessing import Pool

import requests
from pyramid.config import Configurator
from pyramid.response import Response

# begin chdir armor
up = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.dirname(up)
hendrix_app_dir = os.path.dirname(testdir)
hendrix_package_dir = os.path.dirname(hendrix_app_dir)

sys.path.insert(0, hendrix_package_dir)
# end chdir armor

from hendrix.deploy.base import HendrixDeploy
from zope.interface import provider
from twisted.logger import ILogObserver, formatEvent


@provider(ILogObserver)
def simpleObserver(event):
    print(formatEvent(event))


# from twisted.logger import globalLogBeginner
# globalLogBeginner.beginLoggingTo([simpleObserver], redirectStandardIO=False)

def cpu_heavy(heft, label=None):
    count = 0
    previous_count = 0
    start = 1
    previous = start
    one_before_that = 0
    end = heft

    timer_start = time.time()

    while True:
        new = previous + one_before_that
        one_before_that = previous
        previous = new
        count += 1

        if count == end / 2 and end % 2 == 0:
            print("%s halfway: %s" % (label, time.time() - timer_start))
            time.sleep(0)

        if count == end:
            print("%s done: %s" % (label, time.time() - timer_start))
            return


global total_requests
global avg_duration
total_requests = 0
avg_duration = 0


def long():
    global total_requests
    global avg_duration

    previous_duration = (total_requests * avg_duration)
    total_requests += 1

    timer_start = time.time()
    thread = threading.current_thread()
    print("Starting stream %s on %s" % (total_requests, thread.name))
    # cpu_heavy(100000, label)
    r = requests.get('http://localhost:8010/.25')

    duration = time.time() - timer_start
    print("Finished stream %s after %s" % (total_requests, duration))

    avg_duration = float(previous_duration + duration) / float(total_requests)

    print("Average duration after %s: %s" % (total_requests, avg_duration))


class PerformanceTest(object):
    pool = Pool(20)

    def view(self, request):
        # option 1
        # @crosstown_traffic()
        # def wait():
        #     long()

        # option 2

        self.pool.apply_async(long)

        return Response()


config = Configurator()
config.add_route('test_view', '/')
config.add_view(PerformanceTest().view, route_name='test_view')

app = config.make_wsgi_app()

if __name__ == '__main__':
    deployer = HendrixDeploy(options={'wsgi': app})
    deployer.run()
