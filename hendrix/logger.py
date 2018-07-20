import io

from twisted.logger import (
    ILogObserver, jsonFileLogObserver, FilteringLogObserver,
    LogLevelFilterPredicate, LogLevel
)
from zope.interface import provider

from .defaults import DEFAULT_LOG_FILE


@provider(ILogObserver)
def hendrixObserver(path=DEFAULT_LOG_FILE, log_level=LogLevel.warn):
    json_observer = jsonFileLogObserver(
        io.open(path, 'a')
    )
    return FilteringLogObserver(
        json_observer,
        [LogLevelFilterPredicate(log_level), ]
    )
