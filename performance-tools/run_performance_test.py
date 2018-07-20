from __future__ import print_function

import os
import sys
import time
from multiprocessing import Process

from httperfpy import Httperf
from pyramid.config import Configurator
from pyramid.response import Response
from twisted.internet import reactor
from twisted.internet.threads import deferToThread

# begin chdir armor
up = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.dirname(up)
hendrix_app_dir = os.path.dirname(testdir)
hendrix_package_dir = os.path.dirname(hendrix_app_dir)

sys.path.insert(0, hendrix_package_dir)
# end chdir armor
from hendrix.deploy.base import HendrixDeploy
from hendrix.experience import crosstown_traffic

######
# SETTINGS
######

total_calls = 10


class StateMachine(object):

    def __init__(self):
        self.num_calls = 0
        self.num_async_complete = 0


test_state = StateMachine()


def stereotypical_view(request):
    @crosstown_traffic(no_go_status_codes=[])
    def long_thing():
        for i in range(6):
            # print("Making API call number %s" % i)
            time.sleep(.5)
        test_state.num_async_complete += 1
        print("API call %s" % test_state.num_async_complete)
        if test_state.num_async_complete == total_calls:
            print("DONE!")
            reactor.stop()

    reply_message = "Thanks for doing whatever you did!"
    return Response(reply_message)


config = Configurator()
config.add_route('test_view', '/')
config.add_view(stereotypical_view, route_name='test_view')

app = config.make_wsgi_app()
deployer = HendrixDeploy(options={'wsgi': app})


def run_http_battery():
    print("Running HTTP Battery")
    battery = Httperf(
        server="localhost",
        port=8000,
        num_conns=total_calls,
        rate=total_calls,
        timeout=1,
    )

    battery.parser = True
    test_state.results = battery.run()


def http_battery_process():
    p = Process(target=run_http_battery)
    p.start()
    p.join()


def analyze_results(results):
    print(results)


d = deferToThread(http_battery_process)
d.addCallback(analyze_results)
deployer.run()
print("Reactor unblocked.")
