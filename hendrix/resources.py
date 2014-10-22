import sys
import importlib
from hendrix.utils import responseInColor
from twisted.web import resource, static
from twisted.web.server import NOT_DONE_YET
from twisted.web.wsgi import WSGIResource, _WSGIResponse

import logging
import chalk

logger = logging.getLogger(__name__)


class DevWSGIResource(WSGIResource):

    def render(self, request):
        """
        Turn the request into the appropriate C{environ} C{dict} suitable to be
        passed to the WSGI application object and then pass it on.

        The WSGI application object is given almost complete control of the
        rendering process.  C{NOT_DONE_YET} will always be returned in order
        and response completion will be dictated by the application object, as
        will the status, headers, and the response body.
        """
        response = LoudWSGIResponse(
            self._reactor, self._threadpool, self._application, request)
        response.start()
        return NOT_DONE_YET


class LoudWSGIResponse(_WSGIResponse):

    def startResponse(self, status, headers, excInfo=None):
        """
        extends startResponse to call speakerBox in a thread
        """
        if self.started and excInfo is not None:
            raise excInfo[0], excInfo[1], excInfo[2]
        self.status = status
        self.headers = headers
        self.reactor.callInThread(
            responseInColor, self.request, status, headers
        )
        return self.write


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

    def __init__(self, reactor, threads, application, loud=False):
        resource.Resource.__init__(self)
        if loud:
            self.wsgi_resource = DevWSGIResource(reactor, threads, application)
        else:
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

    def putNamedChild(self, res):
        """
        putNamedChild takes either an instance of hendrix.contrib.NamedResource
        or any resource.Resource with a "namespace" attribute as a means of
        allowing application level control of resource namespacing.

        if a child is already found at an existing path,
        resources with paths that are children of those physical paths
        will be added as children of those resources

        """
        try:
            EmptyResource = resource.Resource
            namespace = res.namespace
            parts = namespace.strip('/').split('/')

            # initialise parent and children
            parent = self
            children = self.children
            # loop through all of the path parts except for the last one
            for name in parts[:-1]:
                child = children.get(name)
                if not child:
                    # if the child does not exist then create an empty one
                    # and associate it to the parent
                    child = EmptyResource()
                    parent.putChild(name, child)
                # update parent and children for the next iteration
                parent = child
                children = parent.children

            name = parts[-1]  # get the path part that we care about
            if children.get(name):
                logger.warning(
                    'A resource already exists at this path. Check '
                    'your resources list to ensure each path is '
                    'unique. The previous resource will be overridden.'
                )
            parent.putChild(name, res)
        except AttributeError:
            # raise an attribute error if the resource `res` doesn't contain
            # the attribute `namespace`
            msg = (
                '%r improperly configured. additional_resources instances must'
                ' have a namespace attribute'
            ) % resource
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
        StaticResource = DjangoStaticResource(
            '/abspath/to/static/folder', 'custom-static-relative-url'
        )

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
    chalk.green(
        "Adding media resource for URL '%s' at path '%s'" % (rel_url, path)
    )
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

            additional_resources.append(
                getattr(resource_module, resource_name)
            )

    return additional_resources
