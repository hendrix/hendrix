import io
import unittest

from twisted.internet import reactor
from twisted.logger import eventsFromJSONLogFile

from hendrix.contrib import SettingsError
from hendrix.defaults import *
from hendrix.deploy.base import HendrixDeploy
from hendrix.utils import get_pid

TEST_SETTINGS = 'test.testproject.settings'


def iter_test_logs():
    log_file = io.open(DEFAULT_LOG_FILE)
    for event in eventsFromJSONLogFile(log_file):
        if event.get('log_namespace').startswith('test'):
            yield event


class HendrixTestCase(unittest.TestCase):
    """
    This is where we collect our helper functions to test hendrix
    """

    def setUp(self):
        self.reactor = reactor

    def deploy(self, action, options):
        return HendrixDeploy(action, options, reactor=self.reactor)

    def tearDown(self):
        """
        cleans up the reactor after running startService on a
        twisted.application.service
        """
        test_pid_file = get_pid(
            {'settings': TEST_SETTINGS, 'http_port': HTTP_PORT}
        )
        if os.path.exists(test_pid_file):
            os.remove(test_pid_file)

        self.reactor.disconnectAll()
        return self.reactor.removeAll()

    def wsgiDeploy(self, action='start', options={}):
        """
        Overrides the deploy functionality to test hendrix outside of the
        whole django LazySettings.configure() thing.
        HOWEVER, as the plugin does rely on `from djanog.conf import settings`
        we should test that flow path also...
        """
        if options.get('settings'):
            raise SettingsError("uh uh uh... Don't use settings here.")
        if not options.get('wsgi'):
            options.update({'wsgi': 'test.wsgi'})
        return self.deploy(action, options)

    def settingsDeploy(self, action='start', options={}):
        "Use the hendrix test project to test the bash deployment flow path"
        os.environ['DJANGO_SETTINGS_MODULE'] = TEST_SETTINGS
        options.update({'settings': TEST_SETTINGS})
        return self.deploy(action, options)
