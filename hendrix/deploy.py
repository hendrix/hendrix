import importlib
import os
import sys
from hendrix import HENDRIX_DIR, import_wsgi
from hendrix.parser import HendrixParser
from hendrix.resources import get_additional_resources
from hendrix.services import get_additional_services, HendrixService
from twisted.internet import reactor



class HendrixDeploy(object):

    def __init__(self, action, settings, wsgi, port):
        self.action = action
        self.settings = settings
        self.wsgi = wsgi
        self.port = port
        wsgi_module = import_wsgi(wsgi)
        settings_module = importlib.import_module(settings)
        os.environ['DJANGO_SETTINGS_MODULE'] = settings

        self.service = HendrixService(
            wsgi_module.application, port,
            resources=get_additional_resources(settings_module),
            services=get_additional_services(settings_module)
        )
        getattr(self, action)()

    @property
    def pid(self):
        return '%s/%s_%s.pid' % (
            HENDRIX_DIR, self.port, self.settings.replace('.', '_')
        )

    def start(self):
        with open(self.pid, 'wa') as pid_file:
            pid_file.write('%d' % os.getpid())
        self.service.startService()
        reactor.run()

    def stop(self, sig=9):
        with open(self.pid) as pid_file:
            pids = pid_file.readlines()
            for pid in pids:
                os.kill(int(pid), sig)
        os.remove(self.pid)

    def restart(self, sig=9):
        self.stop(sig)
        self.start()


if __name__ == '__main__':
    parser = HendrixParser().all_args()
    arguments = vars(parser.parse_args())
    HendrixDeploy(**arguments)
