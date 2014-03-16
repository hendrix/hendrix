"""
    Signals for easy use in django projects
"""

import django.dispatch

short_task = django.dispatch.Signal(providing_args=["args", "kwargs"])

long_task = django.dispatch.Signal(providing_args=["args", "kwargs"])

print 'signals loaded'