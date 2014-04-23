from hendrix.management.commands.options import options as hx_options
from hendrix.test import HendrixTestCase
from mock import patch
from twisted.application import service
from twisted.internet import reactor


class DeployTests(HendrixTestCase):
    "Tests HendrixDeploy"

    def test_options_structure(self):
        """
        A test to ensure that HendrixDeploy.options also has the complete set
        of options available
        """
        deploy = self.noSettingsDeploy()
        options = hx_options()
        expected_keys = options.keys()
        actual_keys = deploy.options.keys()
        self.assertListEqual(expected_keys, actual_keys)

    def test_settings_doesnt_break(self):
        """
        A placeholder test to ensure that instantiating HendrixDeploy through
        the hx bash script or the manage.py path wont raise any errors
        """
        self.withSettingsDeploy()

    def test_workers(self):
        "test the expected behaviour of workers and associated functions"
        num_workers = 2
        deploy = self.withSettingsDeploy('start', {'workers': num_workers})
        with patch.object(reactor, 'run') as _run:
            with patch.object(reactor, 'spawnProcess') as _spawnProcess:
                deploy.run()
                self.assertEqual(_spawnProcess.call_count, num_workers)

    def test_no_workers(self):
        deploy = self.withSettingsDeploy()
        with patch.object(reactor, 'run') as _run:
            with patch.object(reactor, 'spawnProcess') as _spawnProcess:
                deploy.run()
                self.assertEqual(_spawnProcess.call_count, 0)

    def test_addHendrix(self):
        "test that addHendrix returns a MulitService"
        deploy = self.withSettingsDeploy()
        deploy.addHendrix()
        self.assertIsInstance(deploy.hendrix, service.MultiService)
