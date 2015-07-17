# initial pass at a `test` log events analyzer
import io
from twisted.logger import eventsFromJSONLogFile
from twisted.logger import extractField

from ..defaults import DEFAULT_LOG_FILE


def iter_test_logs():
    log_file = io.open(DEFAULT_LOG_FILE)
    for event in eventsFromJSONLogFile(log_file):
        if event.get('log_namespace').startswith('hendrix.test'):
            yield event
