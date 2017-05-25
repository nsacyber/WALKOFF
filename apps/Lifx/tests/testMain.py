from unittest import TestCase
from apps.SkeletonApp.main import Main

class TestMain(TestCase):
    def test_function(self):
        app = Main()
        message = app.test_function()
        self.assertDictEqual(message, {})

    def test_function_with_param(self):
        app = Main()
        message = app.test_function_with_param(args={"test_param": "walkoff"})
        self.assertEqual(message, "walkoff")

    def test_function_with_object_reference(self):
        app = Main(name="SkeletonApp", device="test_device")
        message = app.test_function_with_object_reference()
        self.assertEqual(message, "test_device")

