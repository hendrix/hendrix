import imoprtlib
import os
from . import HENDRIX_DIR
from .resources import get_additional_resources
from .services import get_additional_services, HendrixService
from daemonize import Daemonize
from .parser import HendrixParser


class HendrixDeploy(object):

    def __init__(action, settings, wsgi, port):
        settings_module = importlib.import_module(settings)
        self.service = HendrixService(
            wsgi, port,
            resources=get_additional_resources(settings_module),
            services=get_additional_services(settings_module)
        )
        getattr(self, action)()

    @property
    def pid(self):
        return '%s/%s_%s.pid' % (HENDRIX_DIR, port, settings)

    def start(self):
        self.service.startService()
        Daemonize(app='hendrix', action=reactor.run, pid=self.pid).start()


    def stop(self, sig=2):
        with open(self.pid) as pid_file:
            pids = pid_file.readlines()
            for pid in pids:
                os.kill(pid, sig)
        os.remove(self.pid)

    def restart(self, sig=2):
        self.stop(sig)
        self.start()


if __name__ == '__main__':
    parser = HendrixParser().all_args()
    args = vars(parser.parse_args())
    HendrixDeploy(**args)
