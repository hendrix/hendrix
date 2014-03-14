"""
    Signals for easy use in django projects
"""

import django.dispatch

send_message = django.dispatch.Signal(providing_args=["recipient_pool_uid", "data"])

short_task = django.dispatch.Signal(providing_args=["args", "kwargs"])

long_task = django.dispatch.Signal(providing_args=["args", "kwargs"])

print 'signals loaded'