"""
Run these tests using nosetests
"""
import os
import unittest
from hendrix.deploy import HendrixDeploy


class HendrixTestCase(unittest.TestCase):
    """
    This is where we collect our helper functions to test hendrix
    """
    def noSettingsDeploy(self, action='start', options={}):
        """
        Overrides the deploy functionality to test hendrix outside of the
        whole django LazySettings.configure() thing.
        HOWEVER, as the plugin does rely on `from djanog.conf import settings`
        we should test that flow path also...
        """
        options.update({'wsgi': 'hendrix.tests.wsgi'})
        return HendrixDeploy(action, options)

    def withSettingsDeploy(self, action='start', options={}):
        "Use the hendrix test project to test the bash deployment flow path"
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", "hendrix.tests.testproject.settings"
        )
        options.update({'settings': 'hendrix.tests.testproject.settings'})
        return HendrixDeploy(action, options)
