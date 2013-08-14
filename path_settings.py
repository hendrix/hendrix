import sys
from path import path

PROJECT_ROOT = path(__file__).abspath().dirname().dirname()

VIRTUALENV = path(sys.executable).abspath().dirname().dirname()

DEVELOPMENT_ADMIN_MEDIA = "%s/lib/python2.7/site-packages/django/contrib/admin/media" % VIRTUALENV

PRODUCTION_ADMIN_MEDIA = "."
PRODUCTION_STATIC = "."

LOG_DIRECTORY = '.'  # TODO: Obviously not this.


def set_path():
    sys.path.append(PROJECT_ROOT)
