import sys, os, logging.config

from zope.interface import implements
from django.utils import importlib
from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from hendrix.deploy_functions import get_hendrix_resource
import imp


class Options(usage.Options):
    optParameters = [
        ["wsgi", "w", None, "A python module that contains a WSGIHandler instance called wsgi_handler"],
        ["port", "p", None, "The port number to listen on."],
        ["settings", "s", None, "The settings to use for launch."],
    ]


class HendrixServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "hendrix"
    description = "A twisted deployment module for django."
    options = Options

    def makeService(self, options):
        wsgi_module = imp.load_source('wsgi', options['wsgi'])
        
        settings = options['settings']
        os.environ['DJANGO_SETTINGS_MODULE'] = settings_mod_string = settings

        # Use the logger defined in the settings file.
        try:
            settings_module = importlib.import_module(settings_mod_string)
        except ImportError:
            raise RuntimeError("Could not find '%s'." % settings)
        
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
        
        resource, server = get_hendrix_resource(
            wsgi_handler=wsgi_module.get_wsgi_handler(settings),
            settings=settings, 
            port=int(options['port']),
            logger=logger,
        )
        return server

serviceMaker = HendrixServiceMaker()