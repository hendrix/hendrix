from path import path
from twisted.application import service
from unittest import expectedFailure
import imp, importlib
import mock
import unittest
import sys
import wsgi

EGG_ROOT = path(__file__).abspath().dirname()
PACKAGE_ROOT = EGG_ROOT.dirname()
says.path.append(PACKAGE_ROOT)

deploy_plugin_module = imp.load_source('deploy_plugin', "%s/twisted/plugins/deploy_plugin.py" % PACKAGE_ROOT)

WSGI_FILE = "%s/%s.py" % (path(wsgi.__file__).abspath().dirname(), wsgi.__name__)


class ServiceTests(unittest.TestCase):

     service_maker = deploy_plugin_module.HendrixServiceMaker()

     def test_hendrix_service_maker_makes_hendrix_server(self):
         options = {'port': "2000", 'settings': "fake_settings", "wsgi": WSGI_FILE}
         server = self.service_maker.makeService(options)
         self.assertIsInstance(server, service.MultiService)

     def test_no_settings_matching_settings_raises_runtime_error(self):
         options = {'port': "2000", "settings": "does_not_exist", "wsgi": WSGI_FILE}
         self.assertRaises(RuntimeError, self.service_maker.makeService, options)

     '''
     Logging Tests

     The following link is a helpful blog post on examining logging buffer.
     http://plumberjack.blogspot.com/2010/09/unit-testing-and-logging.html
     '''
     @expectedFailure
     def test_no_logging_setting_causes_default_logger(self):
         options = {'port': "2000", 'settings': "test", "wsgi": WSGI_FILE}
         server = self.service_maker.makeService(options)
         self.fail()

     @expectedFailure
     def test_no_logging_setting_causes_warning(self):
        options = {'port': "2000", "settings": "i_didnt_ask_for_santana_abraxas", "wsgi": WSGI_FILE}
        #If the setting module has no LOGGING, we warn them and question of the action they are about to take.
        self.fail()

if __name__ == '__main__':
    unittest.main()