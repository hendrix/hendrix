import os
import sys
import importlib
from twisted.web import resource, static
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
            msg = '%r improperly configured. additional_resources instances must have a namespace attribute'%resource
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
        resource.Resource.__init__(self)
        self.namespace = namespace


    def getChild(self, path, request):
        """
        By default this resource will yield a ForbiddenResource instance unless
        a request is made for a static child i.e. a child added using putChild
        """
        # override this method if you want to serve dynamic child resources
        return resource.ForbiddenResource("This is a resource namespace.")


class MediaResource(static.File):
    '''
    A simple static service with directory listing disabled
    (gives the client a 403 instead of letting them browse
    a static directory).
    '''
    def directoryListing(self):
        # Override to forbid directory listing
        return resource.ForbiddenResource()



def DjangoStaticResource(path, rel_url='static'):
    """
    takes an app level file dir to find the site root and servers static files
    from static
    Usage:
        [...in app.resource...]
        from hendrix.resources import DjangoStaticResource
        StaticResource = DjangoStaticResource('/abspath/to/static/folder')
        ... OR ...
        StaticResource = DjangoStaticResource('/abspath/to/static/folder', 'custom-static-relative-url')

        [...in settings...]
        HENDRIX_CHILD_RESOURCES = (
            ...,
            'app.resource.StaticResource',
            ...
        )
    """
    rel_url = rel_url.strip('/')
    StaticFilesResource = MediaResource(path)
    StaticFilesResource.namespace = rel_url
    return StaticFilesResource


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


