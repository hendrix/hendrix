"""
Run these tests using nosetests
"""
import os
import unittest
from hendrix import deploy
from twisted.internet import reactor
from hendrix.utils import get_pid

from hendrix.defaults import *

TEST_SETTINGS = 'hendrix.test.testproject.settings'


class HendrixTestCase(unittest.TestCase):
    """
    This is where we collect our helper functions to test hendrix
    """

    def tearDown(self):
        """
        cleans up the reactor after running startService on a
        twisted.application.service
        """
        reactor.removeAll()

        test_pid_file = get_pid({'settings':TEST_SETTINGS, 'http_port':HTTP_PORT})
        if os.path.exists(test_pid_file):
            os.remove(test_pid_file)


    def noSettingsDeploy(self, action='start', options={}):
        """
        Overrides the deploy functionality to test hendrix outside of the
        whole django LazySettings.configure() thing.
        HOWEVER, as the plugin does rely on `from djanog.conf import settings`
        we should test that flow path also...
        """
        options.update({'wsgi': 'hendrix.test.wsgi'})
        return deploy.HendrixDeploy(action, options)

    def withSettingsDeploy(self, action='start', options={}):
        "Use the hendrix test project to test the bash deployment flow path"
        os.environ['DJANGO_SETTINGS_MODULE'] = TEST_SETTINGS
        options.update({'settings': TEST_SETTINGS})
        return deploy.HendrixDeploy(action, options)
