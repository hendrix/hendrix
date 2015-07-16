from .defaults import DEFAULT_LOG_FILE
from twisted.logger import (
    ILogObserver, jsonFileLogObserver, FilteringLogObserver,
    LogLevelFilterPredicate, LogLevel, globalLogPublisher
)
from zope.interface import provider

import io


@provider(ILogObserver)
def hendrixObserver(path=DEFAULT_LOG_FILE, log_level=LogLevel.warn):
    json_observer = jsonFileLogObserver(
        io.open(path, 'a')
    )
    return FilteringLogObserver(
        json_observer,
        [LogLevelFilterPredicate(log_level), ]
    )


globalLogPublisher.addObserver(hendrixObserver(log_level=LogLevel.debug))
