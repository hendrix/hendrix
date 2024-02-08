"""
    Signals for easy use in django projects
"""

try:
    from django import dispatch

    short_task = dispatch.Signal()

    long_task = dispatch.Signal()

    message_signal = dispatch.Signal()

    USE_DJANGO_SIGNALS = True

except ImportError:
    USE_DJANGO_SIGNALS = False
