import unittest
from core.validator import *

class TestAppApiValidation(unittest.TestCase):
    """
    This test does not validate if the schema is correct, only the functions associated with further validation
    """
    def setUp(self):
        self.dereferencer = None

    def test_validate_definitions_empty_required_empty_properties(self):
        definition = {'required': [], 'properties': {}}
