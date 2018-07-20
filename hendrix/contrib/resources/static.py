import os

from django.conf import settings
from django.contrib.staticfiles import finders

from hendrix.facilities.resources import DjangoStaticResource


def generate_resources_for_location(disk_root, url):
    for root, dirs, files in os.walk(disk_root):
        yield DjangoStaticResource(
            root,
            url.strip('/') + '%s' % root.split(disk_root)[-1]
        )


class DjangoStaticsFinder(object):
    """
        finds all static resources for this django installation
        and creates a static resource for each's base directory
    """

    namespace = settings.STATIC_URL

    @staticmethod
    def get_resources():

        # add a handler for MEDIA files if configured
        if settings.MEDIA_ROOT and settings.MEDIA_URL:
            yield DjangoStaticResource(
                settings.MEDIA_ROOT, settings.MEDIA_URL
            )

        pipeline_finder = 'pipeline.finders.PipelineFinder'
        has_pipeline_finder = pipeline_finder in settings.STATICFILES_FINDERS
        if not settings.DEBUG or has_pipeline_finder:
            yield DjangoStaticResource(
                settings.STATIC_ROOT, settings.STATIC_URL
            )
        else:
            existing = []
            for finder in finders.get_finders():
                for staticfile, storage in finder.list([]):
                    dirname = os.path.dirname(staticfile)
                    path = os.path.join(storage.base_location, dirname)
                    if path not in existing and dirname:
                        yield DjangoStaticResource(
                            path,
                            settings.STATIC_URL + '%s/' % dirname
                        )

                        existing.append(path)


# The rest is for compatibility with existing code based on the deprecated
# classes below.
try:
    DefaultDjangoStaticResource = DjangoStaticResource(
        settings.STATIC_ROOT, settings.STATIC_URL
    )
except AttributeError:
    raise AttributeError(
        "Please make sure you have assigned your STATIC_ROOT and STATIC_URL"
        " settings"
    )

try:
    from django.contrib import admin

    admin_media_path = os.path.join(admin.__path__[0], 'static/admin/')
    DjangoAdminStaticResource = DjangoStaticResource(
        admin_media_path, settings.STATIC_URL + 'admin/'
    )
except:
    raise
