# from unittest import TestCase
# from apps.EthereumBlockchain import main
#
#
# class TestMain(TestCase):
#     def setUp(self):
#         self.app = main.Main()
#
#     def test_create_and_set_up_network(self):
#         args = {'total_nodes': 3}
#         self.app.create_accounts(args)
#         self.app.set_up_network(args)
#
#     def test_submit_greeting(self):
#         # Assume network is running
#         args = {"greeting": "Hello human user!"}
#         self.assertTrue(self.app.submit_greeting(args) == 0)