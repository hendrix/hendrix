import sys, os
from pyramid.config import Configurator
from pyramid.response import Response
import time

# begin chdir armor
from hendrix.contrib.async.resources import MessageResource

up = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.dirname(up)
hendrix_app_dir = os.path.dirname(testdir)
hendrix_package_dir = os.path.dirname(hendrix_app_dir)
# end chdir armor

sys.path.insert(0, hendrix_package_dir)
print sys.path

from hendrix.deploy.base import HendrixDeploy
from hendrix.experience import crosstown_traffic


def fib_view(request):

    @crosstown_traffic(same_thread=True)
    def fib():
        count = 0
        previous_count = 0
        start = 1
        previous = start
        one_before_that = 0
        once_in_a_while = 500000

        label = request.matchdict['label']

        timer_start = time.time()

        while True:

            new = previous + one_before_that
            one_before_that = previous
            previous = new
            count += 1
            if count % once_in_a_while == 0:
                timer_end = time.time()
                print "%s : %s" % (label, timer_end - timer_start)

                timer_start = time.time()
                previous = start
                one_before_that = 0

    return Response('Starting Fibonacci %(label)s!' % request.matchdict)

if __name__ == '__main__':
    config = Configurator()
    config.add_route('fib', '/fib/{label}')
    config.add_view(fib_view, route_name='fib')

    app = config.make_wsgi_app()
    deployer = HendrixDeploy(options={'wsgi': app})
    deployer.resources.append(MessageResource)
    deployer.run()
