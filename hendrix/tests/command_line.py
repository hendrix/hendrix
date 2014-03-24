import unittest

__package__ = 'hendrix.command_line'
import hendrix
from ..hendrix_deploy import HendrixAction, process

@unittest.skip  # doesn't currently test anything of value
class TestArgumentProcessing(unittest.TestCase):

    good_start_arguments = {'ACTION': 'start', 'WSGI': 'wsgi.py',
    'PORT': '8000', 'SETTINGS': 'settings'}
    wrong_order_arguments = {'ACTION': 'stop', 'WSGI': '8000',
         'PORT': 'settings', 'SETTINGS': 'wsgi.py'}
    good_instance = process(good_start_arguments)
    bad_instance = process(wrong_order_arguments)

    def test_action_argument_equals_hendrix_action_argument(self):
        self.assertEqual(self.good_instance.action, 'start')

    def test_wrong_arguments_something(self):
        self.assertNotEqual(self.bad_instance.wsgi, '8000')

if __name__ == '__main__':
    unittest.main()
