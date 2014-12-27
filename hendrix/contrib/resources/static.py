import os
from hendrix.resources import DjangoStaticResource
from django.conf import settings
from django.contrib.staticfiles import finders



class DjangoStaticsFinder:
    """ 
        finds all static resources for this django installation
        and creates a static resource for each's base directory 
    """

    namespace = settings.STATIC_URL

    @staticmethod
    def get_resources():

        ignore_patterns = [
            '*.less',
            '*.scss',
            '*.styl',
        ]

        existing = []
        for finder in finders.get_finders():
            for _, storage in finder.list([]):
                if not storage.base_location in existing:
                    yield DjangoStaticResource(
                        storage.location,
                        settings.STATIC_URL + '%s/' % storage.base_location
                    )

"""
The rest is for compatibility with existing code based on the deprecated
classes below.

"""
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
        admin_media_path, settings.STATIC_URL+'admin/'
    )
except:
    raise

