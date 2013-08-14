import unittest
from twisted.plugins import deploy_plugin
import mock
from twisted.application import internet, service
from unittest import expectedFailure

class MockSettings(object):
    LOGGING = {
    'version': 1,
    }
    
    def __init__(self, settings_mod_string, *args, **kwargs):
        if settings_mod_string == "settings.i_didnt_ask_for_santana_abraxas":
            raise ImportError()
        
        if settings_mod_string == "without_logging":
            pass # see test_no_logging_setting_causes_warning below
            
            
        return super(MockSettings, self).__init__(*args, **kwargs)    
@mock.patch("django.utils.importlib.import_module", MockSettings)
class ServiceTests(unittest.TestCase):
     
     service_maker = deploy_plugin.HendrixServiceMaker()
     
     def test_hendrix_service_maker_makes_hendrix_server(self):
         options = {'port': "2000", 'deployment_type': "test"}
         server = self.service_maker.makeService(options)
         self.assertIsInstance(server, service.MultiService)
     
     def test_no_settings_matching_deployment_type_raises_runtime_error(self):
         options = {'port': "2000", "deployment_type": "i_didnt_ask_for_santana_abraxas"}
         self.assertRaises(RuntimeError, self.service_maker.makeService, options)
     
     '''
     Logging Tests
     
     The following link is a helpful blog post on examining logging buffer.
     http://plumberjack.blogspot.com/2010/09/unit-testing-and-logging.html
     '''
     @expectedFailure
     def test_no_logging_setting_causes_default_logger(self):
         options = {'port': "2000", 'deployment_type': "test"}
         server = self.service_maker.makeService(options)
         self.fail()

     @expectedFailure
     def test_no_logging_setting_causes_warning(self):
        options = {'port': "2000", "deployment_type": "i_didnt_ask_for_santana_abraxas"}
        #If the setting module has no LOGGING, we warn them and question of the action they are about to take.
        self.fail()
     
if __name__ == '__main__':
    unittest.main()