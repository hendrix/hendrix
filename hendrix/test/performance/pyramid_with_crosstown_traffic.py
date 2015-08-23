import sys, os
import threading
from pyramid.config import Configurator
from pyramid.response import Response
import time

# begin chdir armor
up = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.dirname(up)
hendrix_app_dir = os.path.dirname(testdir)
hendrix_package_dir = os.path.dirname(hendrix_app_dir)

sys.path.insert(0, hendrix_package_dir)
# end chdir armor

from hendrix.deploy.base import HendrixDeploy
from hendrix.experience import crosstown_traffic
from hendrix.contrib.async.resources import MessageResource
from zope.interface import provider
from twisted.logger import ILogObserver, formatEvent

@provider(ILogObserver)
def simpleObserver(event):
    print(formatEvent(event))

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
            print "%s halfway: %s" % (label, time.time() - timer_start)
            time.sleep(0)

        if count == end:
            print "%s done: %s" % (label, time.time() - timer_start)
            return


def fib_view(request):

    label = request.matchdict['label']
    stream_thread = threading.current_thread()
    print "Received request %s on thread %s" % (label, stream_thread.name)

    @crosstown_traffic(same_thread=False,
                       always_spawn_worker=True)
    def wait():
        timer_start = time.time()
        thread = threading.current_thread()
        print "Starting label %s on %s" % (label, thread.name)
        cpu_heavy(590000, label)
        # r = requests.get('http://localhost:8010/2')
        print "Finished label %s after %s" % (label, time.time() - timer_start)

    print "Returning response for %s" % label

    return Response('Starting Fibonacci %(label)s!' % request.matchdict)

if __name__ == '__main__':
    config = Configurator()
    config.add_route('fib', '/fib/{label}')
    config.add_view(fib_view, route_name='fib')

    app = config.make_wsgi_app()
    deployer = HendrixDeploy(options={'wsgi': app})
    deployer.resources.append(MessageResource)
    deployer.run()
