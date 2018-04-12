from unittest import TestCase
from mock import patch
from walkoff.appgateway.console import ConsoleLoggingHandler
from logging import WARN
from walkoff.events import WalkoffEvent


class TestConsoleLoggingHandler(TestCase):

    @patch.object(WalkoffEvent.CommonWorkflowSignal, 'send')
    def test_emit(self, mock_send):
        handler = ConsoleLoggingHandler()
        handler.level = WARN

        def mock_format(record):
            return record

        handler.format = mock_format

        record = 'some test string'
        handler.emit(record)
        mock_send.assert_called_once_with(handler, event=WalkoffEvent.ConsoleLog, message=record, level=WARN)
