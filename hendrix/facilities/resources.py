import sys

import chalk
from twisted.logger import Logger
from twisted.web import resource, static
from twisted.web.server import NOT_DONE_YET
from twisted.web.wsgi import WSGIResource

from hendrix.facilities.response import HendrixWSGIResponse, LoudWSGIResponse


class HendrixWSGIResource(WSGIResource):
    ResponseClass = HendrixWSGIResponse

    def render(self, request):
        response = self.ResponseClass(
            self._reactor, self._threadpool, self._application, request)
        response.start()
        return NOT_DONE_YET


class DevWSGIResource(HendrixWSGIResource):
    ResponseClass = LoudWSGIResponse


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

    logger = Logger()

    def __init__(self, reactor, threads, application, loud=False):
        resource.Resource.__init__(self)
        if loud:
            self.wsgi_resource = DevWSGIResource(reactor, threads, application)
        else:
            self.wsgi_resource = HendrixWSGIResource(reactor, threads, application)

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
                self.logger.warn(
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
            raise AttributeError(msg, None, sys.exc_info()[2])


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
