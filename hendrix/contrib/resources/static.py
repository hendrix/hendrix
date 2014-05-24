import os
from hendrix.resources import DjangoStaticResource
from django.conf import settings


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
