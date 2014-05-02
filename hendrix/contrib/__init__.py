import importlib
from twisted.web.resource import Resource, ForbiddenResource
from .async.resources import MessageResource


class SettingsError(Exception):
    "Because we don't to inherit ImproperlyConfigured..."
    pass



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
