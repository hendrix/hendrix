from hendrix.management.commands.options import options as hx_options
from hendrix.tests import HendrixTestCase


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

    def test_multiprocessing(self):
        # not sure how to test this
        pass
