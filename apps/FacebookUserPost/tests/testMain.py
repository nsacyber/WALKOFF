# from unittest import TestCase, skipIf
# from apps.FacebookUserPost import main
# import sys
#
#
# class TestMain(TestCase):
#     def setUp(self):
#         self.app = main.Main()
#
#     @skipIf(sys.version_info[0] == 3 and sys.version_info[1] == 6, 'Python 3.6.1 is not supported')
#     def test_add_fb_user_and_post_to_wall(self):
#         args = {"user_access_token": "Get from Facebook Developer Account",
#                 "user_id": "me"}
#         self.assertEqual(self.app.add_facebook_user(args), 0)
#
#         args = {"message": "Explore WALKOFF\nat https://github.com/iadgov/WALKOFF\n :D :D :D :D :D"}
#         self.assertTrue("id" in self.app.post_to_user_wall(args))
