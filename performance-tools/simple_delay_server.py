import os
import sys
import time

from pyramid.config import Configurator
from pyramid.response import Response
from twisted.internet import reactor
from twisted.python.threadpool import ThreadPool

tp = reactor.suggestThreadPoolSize(1000)

# begin chdir armor
up = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.dirname(up)
hendrix_app_dir = os.path.dirname(testdir)
hendrix_package_dir = os.path.dirname(hendrix_app_dir)
sys.path.insert(0, hendrix_package_dir)
# end chdir armor

from hendrix.deploy.base import HendrixDeploy

import threading


def delay(request):
    delay_time = float(request.matchdict['seconds'])
    print
    "Thread %s sleeping for %s seconds" % (threading.current_thread(), delay_time)
    time.sleep(delay_time)
    return Response('')


if __name__ == '__main__':
    config = Configurator()
    config.add_route('delay', '/{seconds}')
    config.add_view(delay, route_name='delay')

    app = config.make_wsgi_app()
    tp = ThreadPool(name="Big and Slow.", maxthreads=1000)
    deployer = HendrixDeploy(options={'wsgi': app, 'http_port': 8010}, threadpool=tp)
    deployer.run()
