import chalk
import os
import sys
import importlib
try:
    from django.core.handlers.wsgi import WSGIHandler
except ImportError as e:
    raise ImportError(
        str(e) + '\n' +
        'Hendrix is a Django plugin. As such Django must be installed.'
    ), None, sys.exc_info()[2]
from twisted.web.resource import Resource, ForbiddenResource
from .async.resources import MessageResource


class DevWSGIHandler(WSGIHandler):
    def __call__(self, *args, **kwargs):
        response = super(DevWSGIHandler, self).__call__(*args, **kwargs)
        code = response.status_code
        message = 'Response [%s] => Request %s:%s %s %s on pid %d' % (
            code,
            args[0]['REMOTE_ADDR'],
            args[0]['SERVER_PORT'],
            args[0]['REQUEST_METHOD'],
            args[0]['PATH_INFO'],
            os.getpid()
        )
        signal = code/100
        if signal == 2:
            chalk.green(message)
        elif signal == 3:
            chalk.blue(message)
        else:
            chalk.red(message)
        return response





class NamedResource(Resource):
    """
    A resource that can be used to namespace other resources. Expected usage of
    this resource in a django application is:
        ... in myproject.myapp.somemodule ...
            NamespacedRes = NamedResource('some-namespace')
            NamespacedRes.putChild('namex', SockJSResource(FactoryX...))
            NamespacedRes.putChild('namey', SockJSResource(FactoryY...))
        ... then in settings ...
            HENDRIX_CHILD_RESOURCES = (
              'myproject.myapp.somemodule.NamespacedRes',
              ...,
            )
    """
    def __init__(self, namespace):
        Resource.__init__(self)
        self.namespace = namespace


    def getChild(self, path, request):
        """
        By default this resource will yield a ForbiddenResource instance unless
        a request is made for a static child i.e. a child added using putChild
        """
        # override this method if you want to serve dynamic child resources
        return ForbiddenResource("This is a resource namespace.")


def get_additional_resources(settings_module):
    """
        if HENDRIX_CHILD_RESOURCES is specified in settings_module,
        it should be a list resources subclassed from hendrix.contrib.NamedResource

        example:

            HENDRIX_CHILD_RESOURCES = (
              'apps.offload.resources.LongRunningProcessResource',
              'apps.chat.resources.ChatResource',
            )
    """

    additional_resources = []

    if hasattr(settings_module, 'HENDRIX_CHILD_RESOURCES'):

        for module_path in settings_module.HENDRIX_CHILD_RESOURCES:
            path_to_module, resource_name = module_path.rsplit('.', 1)
            resource_module = importlib.import_module(path_to_module)

            additional_resources.append(getattr(resource_module, resource_name))
    return additional_resources


# Helper resource for the lazy amongst us
HendrixResource = NamedResource('hendrix')
HendrixResource.putChild('message', MessageResource)
# add more resources here ...
