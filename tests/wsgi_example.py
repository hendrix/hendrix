import sys
from path import path

from django.core.handlers.wsgi import WSGIHandler
from raven.contrib.django.raven_compat.middleware.wsgi import Sentry

PROJECT_ROOT = path(__file__).abspath().dirname()
sys.path.append(PROJECT_ROOT)

application = Sentry(WSGIHandler())