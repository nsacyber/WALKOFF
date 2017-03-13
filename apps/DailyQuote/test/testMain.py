from unittest import TestCase
from apps.DailyQuote import main


class TestMain(TestCase):
    def setUp(self):
        self.app = main.Main()

    def test_quote_message(self):
        message = self.app.quoteIntro()
        self.assertDictEqual(message, {"message": "Quote App"})

    def test_quote_message(self):
        quote = self.app.getQuote()
        self.assertEqual(quote["success"], { "total": 1 })

    def test_repeat_to_me(self):
        args = {'call': (lambda: 'test_message')}
        self.assertEqual(self.app.repeatBackToMe(args), 'REPEATING: {0}'.format('test_message'))

    # def test_plus_one(self):
    #     args = {'number': (lambda: '4')}
    #     self.assertEqual(self.app.returnPlusOne(args), '5')
    #     with self.assertRaises(ValueError):
    #         self.app.returnPlusOne({'number': (lambda: 'aa')})
    #
    # def test_shutdown(self):
    #     self.assertIsNone(self.app.shutdown())

