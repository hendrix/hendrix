import os
import imp
import importlib
from path import path

from zope.interface import implements
from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from hendrix.core import get_hendrix_resource


class Options(usage.Options):
    optParameters = [
        ["wsgi", "w", None, "The path to a python module that contains a WSGIHandler instance."],
        ["port", "p", None, "The port number to listen on."],
        ["settings", "s", None, "The settings to use for launch."],
    ]


class HendrixServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "hendrix"
    description = "A twisted deployment module for django."
    options = Options

    def makeService(self, options):
        wsgi_path = path(options['wsgi']).abspath()
        if not wsgi_path.exists():
            raise RuntimeError('%s does not exist' % wsgi_path)
        wsgi_filename = wsgi_path.basename().splitext()[0]
        wsgi_dir = wsgi_path.parent
        try:
            _file, pathname, desc = imp.find_module(wsgi_filename, [wsgi_dir,])
            wsgi_module = imp.load_module(wsgi_filename, _file, pathname, desc)
            _file.close()
        except ImportError:
            raise RuntimeError('Could not import %s' % wsgi_path)

        settings = options['settings']
        os.environ['DJANGO_SETTINGS_MODULE'] = settings

        # Use the logger defined in the settings file.
        try:
            settings_module = importlib.import_module(settings)
        except ImportError:
            raise RuntimeError("Could not find '%s'." % settings)

        resource, server = get_hendrix_resource(
            application=wsgi_module.application,
            settings_module=settings_module,
            port=int(options['port'])
        )
        return server


serviceMaker = HendrixServiceMaker()
