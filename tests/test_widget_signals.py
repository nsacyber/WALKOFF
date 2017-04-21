import unittest
from core.widgetsignals import create_widget_signal_name, get_widget_signal, _widget_signals
from blinker import NamedSignal


class TestWidgetSignals(unittest.TestCase):

    def test_create_widget_signal_name(self):
        input_output = {('', ''): '-',
                       ('', 'bb'): '-bb',
                       ('aa', 'bb'): 'aa-bb',
                       ('aa', ''): 'aa-'}
        for (app_name, widget_name), expected_output in input_output.items():
            self.assertEqual(create_widget_signal_name(app_name, widget_name), expected_output)

    def test_get_widget(self):
        signal = get_widget_signal('aa', 'bb')
        self.assertIsInstance(signal, NamedSignal)
        self.assertEqual(signal.name, create_widget_signal_name('aa', 'bb'))
        self.assertIn(('aa', 'bb'), _widget_signals)

        signal2 = get_widget_signal('aa', 'bb')
        self.assertIs(signal, signal2)
        self.assertEqual(len(_widget_signals), 1)

        signal3 = get_widget_signal('aa', 'cc')
        self.assertEqual(signal3.name, create_widget_signal_name('aa', 'cc'))
        self.assertEqual(len(_widget_signals), 2)

