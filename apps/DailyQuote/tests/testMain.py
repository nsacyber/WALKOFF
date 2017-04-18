from unittest import TestCase
from apps.DailyQuote import main


class TestMain(TestCase):
    def setUp(self):
        self.app = main.Main()

    def test_quote_intro(self):
        message = self.app.quoteIntro()
        self.assertDictEqual(message, {"message": "Quote App"})

    def test_get_quote(self):
        quote = self.app.getQuote()
        if 'success' in quote:
            self.assertEqual(quote["success"], {"total": 1})
        else:
            self.assertIn('error', quote)

    def test_other_quote(self):
        url = "http://api.forismatic.com/api/1.0/"
        args = {'url': (lambda: url)}
        quote = self.app.forismaticQuote(args)
        self.assertIn('success', quote)
        if not quote['success']:
            self.assertIn('text', quote)

    def test_repeat_to_me(self):
        args = {'call': (lambda: 'test_message')}
        self.assertEqual(self.app.repeatBackToMe(args), 'REPEATING: {0}'.format('test_message'))

    def test_shutdown(self):
        self.assertIsNone(self.app.shutdown())
