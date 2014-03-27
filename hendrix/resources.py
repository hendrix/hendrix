import sys
import importlib
from .contrib.async.resources import MessageResource
from twisted.web import resource
from twisted.web.wsgi import WSGIResource


import logging

logger = logging.getLogger(__name__)


class HendrixResource(resource.Resource):
    """
    HendrixResource initialises a WSGIResource and stores it as wsgi_resource.
    It also overrides its own getChild method so to only serve wsgi_resource.
    This means that only the WSGIResource is able to serve dynamic content from
    the root url "/". However it is still possible to extend the resource tree
    via putChild. This is due the fact that getChildFromRequest checks for
    children of the resource before handling the dynamic content (through
    getChild). The modified getChild resource on HendrixResource also restores
    the request.postpath list to its original state. This is essentially a hack
    to ensure that django always gets the full path.
    """

    def __init__(self, reactor, threads, application):
        resource.Resource.__init__(self)
        self.wsgi_resource = WSGIResource(reactor, threads, application)

    def getChild(self, name, request):
        """
        Postpath needs to contain all segments of
        the url, if it is incomplete then that incomplete url will be passed on
        to the child resource (in this case our wsgi application).
        """
        request.prepath = []
        request.postpath.insert(0, name)
        # re-establishes request.postpath so to contain the entire path
        return self.wsgi_resource

    def putNamedChild(self, resource):
        """
        putNamedChild takes either an instance of hendrix.contrib.NamedResource
        or any resource.Resource with a "namespace" attribute as a means of
        allowing application level control of resource namespacing.
        """
        try:
            path = resource.namespace
            self.putChild(path, resource)
        except AttributeError, e:
            msg = 'additional_resources instances must have a namespace attribute'
            raise AttributeError(msg), None, sys.exc_info()[2]



class NamedResource(resource.Resource):
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
        return resource.ForbiddenResource("This is a resource namespace.")




class NamedMediaResource(static.File):
    "Serves files from a directory and forbids access to subpaths"

    def __init__(self, directory, namespace):
        static.File.__init__(directory)
        self.namespace = namespace

    def directoryListing(self):
        # Override to forbid directory listing
        return resource.ForbiddenResource()



class DjangoStaticResource(NamedMediaResource):

    def __init__(self, settings):
        try:
            directory = settings.STATIC_ROOT
            namespace = settings.STATIC_URL.strip('/')
            NamedMediaResource.__init__(directory, namespace)
        except AttributeError, e:
            print e
            raise NotImplementedError(
                'STATIC_ROOT and STATIC_URL must be included in settings.'
            )


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


# Helper resources for the lazy amongst us
HendrixResource = NamedResource('hendrix')
HendrixResource.putChild('message', MessageResource)
# add more resources here ...
