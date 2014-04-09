from hendrix.resources import DjangoStaticResource

from django.conf import settings


DefaultDjangoStaticResource = DjangoStaticResource(settings.STATIC_ROOT, settings.STATIC_URL)