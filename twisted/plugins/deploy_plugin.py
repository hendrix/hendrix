import sys, os, logging.config

from zope.interface import implements
from django.utils import importlib
from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from hendrix.deploy_functions import get_hendrix_resource


class Options(usage.Options):
    optParameters = [["port", "p", None, "The port number to listen on."],
                     ["deployment_type", "dt", None, "The type of deployment instance to launch."],
                     ]

class HendrixServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "hendrix"
    description = "A twisted deployment module for django."
    options = Options

    def makeService(self, options):
        deployment_type = options['deployment_type']
        os.environ['DJANGO_SETTINGS_MODULE'] = settings_mod_string = "settings.%s" % deployment_type

        # Use the logger defined in the settings file.
        try:
            settings_module = importlib.import_module(settings_mod_string)
        except ImportError:
            raise RuntimeError('You must have a settings file that matches the deployment type.  (In this case, %s).' % deployment_type)
        
        try:
            logging.config.dictConfig(settings_module.LOGGING)
            logger = logging.getLogger('DeploymentActions')
        except NameError:
            # Only used if no logger is passed from plugin.
            DEFAULT_LOGGER = logging.getLogger(__name__)
            DEFAULT_LOGGER.warning("Really?  You don't have LOGGING defined in your settings?  It's been around since Django 1.3\n\
            It's probably a good idea to read https://docs.djangoproject.com/en/dev/topics/logging/ and go set it before you try to deploy.")
            logger = DEFAULT_LOGGER
        logger.debug("using python binary: %s" % sys.executable)
        
        resource, application, server = get_hendrix_resource(
                                            deployment_type=deployment_type, 
                                            port=int(options['port']),
                                            logger=logger,
                                        )
        return server

serviceMaker = HendrixServiceMaker()