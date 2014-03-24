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


class DevWSGIHandler(WSGIHandler):
    def __call__(self, *args, **kwargs):
        response = super(DevWSGIHandler, self).__call__(*args, **kwargs)
        print 'Response [%s] - %s:%s %s %s' % (
            response.status_code,
            args[0]['REMOTE_ADDR'],
            args[0]['SERVER_PORT'],
            args[0]['REQUEST_METHOD'],
            args[0]['PATH_INFO'],
        )
        return response


class NamespaceResource(Resource):
    """
    A resource that can be used to namespace other resources. Expected usage of
    this resource in a django application is:
        namespace_res = NamespaceResource('some-namespace')
        namespace_res.putChild('namex', SockJSResource(FactoryX...))
        namespace_res.putChild('namey', SockJSResource(FactoryY...))
        ...
    """
    def __init__(self, namespace='hendrixchildren'):
        super(NamespaceResource, self).__init__()
        self.namespace = namespace


    def getChild(self, path, request):
        """
        By default this resource will yield a ForbiddenResource instance unless
        a request is made for a static child i.e. a child added using putChild
        """
        return ForbiddenResource("This is a resource namespace.")


def get_additional_handlers(settings_module):

    """
        if HENDRIX_EXTRA_HANDLERS is specified in settings_module,
        it should be a list of tuples specifying a url path and a module path
        to a function which returns the handler that will process calls to that url

        example:

            HENDRIX_CHILD_HANDLERS = (
              ('process', 'apps.offload.handlers.get_LongRunningProcessHandler'),
              ('chat',    'apps.chat.handlers.get_ChatHandler'),
            )

            HENDRIX_CHILD_HANDLER_NAMESPACE = 'crosstowntraffic'#(optional)
    """

    additional_handlers = []

    if hasattr(settings_module, 'HENDRIX_CHILD_HANDLERS'):
        namespace = getattr(settings_module,'HENDRIX_CHILD_NAMESPACE','hendrixchildren')

        for url_path, module_path in settings_module.HENDRIX_CHILD_HANDLERS:
            path_to_module, handler_generator = module_path.rsplit('.', 1)
            handler_module = importlib.import_module(path_to_module)

            #TODO:
            #
            #   ideally, we would namespace these handlers like this:
            #   /hendrixchildren/chat
            #   /hendrixchildren/processupdates
            #
            #   this should seemingly be done by creating nested proxy handlers
            #   which would have their own children
            #   for their child paths.
            #

            additional_handlers.append(('%s-%s'%(namespace,url_path), getattr(handler_module, handler_generator)()))
    return additional_handlers
