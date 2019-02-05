"""
    Signals for easy use in django projects
"""

try:
    from django import dispatch

    short_task = dispatch.Signal(providing_args=["args", "kwargs"])

    long_task = dispatch.Signal(providing_args=["args", "kwargs"])

    message_signal = dispatch.Signal(providing_args=["data", "dispatcher"])

    USE_DJANGO_SIGNALS = True

except ImportError:
    USE_DJANGO_SIGNALS = False