import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test.testproject.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
