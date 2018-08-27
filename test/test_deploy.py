from .utils import HendrixTestCase

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
from twisted.application import service
from twisted.internet import tcp

from twisted.logger import Logger

log = Logger()


class DeployTests(HendrixTestCase):
    "Tests HendrixDeploy"

    def test_settings_doesnt_break(self):
        """
        A placeholder test to ensure that instantiating HendrixDeploy through
        the hx bash script or the manage.py path wont raise any errors
        """
        self.settingsDeploy()

    def test_workers(self):
        "test the expected behaviour of workers and associated functions"
        num_workers = 2
        deploy = self.settingsDeploy('start', {'workers': num_workers})
        with patch.object(deploy.reactor, 'spawnProcess') as _spawnProcess:
            deploy.addServices()
            deploy.start()
            self.assertEqual(_spawnProcess.call_count, num_workers)

    def test_no_workers(self):
        deploy = self.settingsDeploy()
        with patch.object(deploy.reactor, 'spawnProcess') as _spawnProcess:
            deploy.addServices()
            deploy.start()
            self.assertEqual(_spawnProcess.call_count, 0)

    def test_addHendrix(self):
        "test that addHendrix returns a MulitService"
        deploy = self.settingsDeploy()
        deploy.addHendrix()
        self.assertIsInstance(deploy.hendrix, service.MultiService)

    def test_flask_deployment(self):
        deploy = self.wsgiDeploy(options={'wsgi': 'test.flasky.app'})
        deploy.addServices()
        deploy.start()
        readers = deploy.reactor.getReaders()
        tcp_readers = [p for p in readers if isinstance(p, tcp.Port)]
        ports = [p.port for p in tcp_readers]
        self.assertTrue(8000 in ports)
