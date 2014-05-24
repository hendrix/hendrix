"""
    Signals for easy use in django projects
"""

from django import dispatch

short_task = dispatch.Signal(providing_args=["args", "kwargs"])

long_task = dispatch.Signal(providing_args=["args", "kwargs"])

message_signal = dispatch.Signal(providing_args=["data", "dispatcher"])
