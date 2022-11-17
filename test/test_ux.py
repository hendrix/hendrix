import os
import sys

from hendrix import ux
from hendrix.contrib import SettingsError
from hendrix.deploy.base import HendrixDeploy
from hendrix.options import options as hx_options
from .utils import HendrixTestCase

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class TestMain(HendrixTestCase):

    def setUp(self):
        super(TestMain, self).setUp()
        self.DEFAULTS = hx_options()
        os.environ['DJANGO_SETTINGS_MODULE'] = ''
        self.devnull = open(os.devnull, 'w')
        self.args_list = ['hx', 'start']
        self.patcher = patch('hendrix.ux.findSettingsModule')
        self.patcher.start()

    def tearDown(self):
        super(TestMain, self).tearDown()
        self.devnull.close()
        self.patcher.stop()

    def test_settings_from_system_variable(self):
        django_settings = 'django.inanity'
        with patch('hendrix.ux.findSettingsModule') as findSettingsMod:
            findSettingsMod.return_value = django_settings
            options = self.DEFAULTS
            self.assertEqual(options['settings'], '')
            options = ux.djangoVsWsgi(options)
            self.assertEqual(options['settings'], django_settings)

    def test_settings_wsgi_absense(self):
        with patch('hendrix.ux.findSettingsModule') as findSettingsMod:
            findSettingsMod.return_value = ""
            self.assertRaises(SettingsError, ux.djangoVsWsgi, self.DEFAULTS)

    def test_user_settings_overrides_system_variable(self):
        django_settings = 'django.inanity'
        with patch('hendrix.ux.findSettingsModule') as findSettingsMod:
            findSettingsMod.return_value = django_settings
            options = self.DEFAULTS
            user_settings = 'myproject.settings'
            options['settings'] = user_settings
            self.assertEqual(options['settings'], user_settings)
            options = ux.djangoVsWsgi(options)
            self.assertEqual(options['settings'], user_settings)

    def test_wsgi_correct_wsgi_path_works(self):
        wsgi_dot_path = 'test.wsgi'
        options = self.DEFAULTS
        options.update({'wsgi': wsgi_dot_path})
        options = ux.djangoVsWsgi(options)
        self.assertEqual(options['wsgi'], wsgi_dot_path)

    def test_wsgi_wrong_path_raises(self):
        wsgi_dot_path = '_this.leads.nowhere.man'

        self.assertRaises(ImportError, HendrixDeploy.importWSGI, wsgi_dot_path)

    def test_cwd_exposure(self):
        cwd = os.getcwd()
        _path = sys.path
        sys.path = [p for p in _path if p != cwd]
        self.assertTrue(cwd not in sys.path)
        ux.exposeProject(self.DEFAULTS)
        self.assertTrue(cwd in sys.path)

    def test_pythonpath(self):
        options = self.DEFAULTS
        test_path = os.path.join(
            os.path.dirname(os.getcwd()),
            'hendrix/test/testproject'
        )
        options['pythonpath'] = test_path
        ux.exposeProject(options)
        self.assertTrue(test_path in sys.path)
        sys.path = [p for p in sys.path if p != test_path]

    def test_shitty_pythonpath(self):
        options = self.DEFAULTS
        test_path = '/if/u/have/this/path/you/suck'
        options['pythonpath'] = test_path
        self.assertRaises(IOError, ux.exposeProject, options)

    def test_dev_friendly_options(self):
        options = self.DEFAULTS
        options['dev'] = True
        self.assertFalse(options['reload'])
        self.assertFalse(options['loud'])
        options = ux.devFriendly(options)
        self.assertTrue(options['reload'])
        self.assertTrue(options['loud'])

    def test_noise_control_daemonize(self):
        options = self.DEFAULTS
        options['quiet'] = True
        options['daemonize'] = True
        stdout = sys.stdout
        stderr = sys.stderr
        redirect = ux.noiseControl(options)
        self.assertEqual(sys.stdout.name, stdout.name)
        self.assertEqual(sys.stderr.name, stderr.name)

        self.assertEqual(redirect, None)

    def test_noise_control_traceback(self):
        options = self.DEFAULTS
        options['quiet'] = True
        options['daemonize'] = True
        options['traceback'] = True
        stdout = sys.stdout
        stderr = sys.stderr
        redirect = ux.noiseControl(options)
        self.assertEqual(sys.stdout.name, stdout.name)
        self.assertEqual(sys.stderr.name, stderr.name)

        self.assertEqual(redirect, None)

    def test_options_structure(self):
        """
        A test to ensure that HendrixDeploy.options also has the complete set
        of options available
        """
        deploy = self.wsgiDeploy()
        expected_keys = self.DEFAULTS.keys()
        actual_keys = deploy.options.keys()
        self.assertEqual(expected_keys, actual_keys)
