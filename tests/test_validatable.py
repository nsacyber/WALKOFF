from unittest import TestCase

from walkoff.executiondb.validatable import Validatable


class MockValidatableNoChildren(Validatable):
    def __init__(self, errors=None):
        self.errors = errors
        self.validate_count = 0

    def validate(self):
        self.validate_count += 1


class MockValidatableWithChildren(Validatable):
    children = ['child_a', 'child_b']

    def __init__(self, child_a, child_b, errors=None):
        self.child_a = child_a
        self.child_b = child_b
        self.errors = errors
        self.validate_count = 0

    def validate(self):
        self.validate_count += 1


class TestValidatable(TestCase):

    def test_is_valid_no_children_no_errors(self):
        obj = MockValidatableNoChildren()
        self.assertTrue(obj._is_valid)

    def test_is_valid_no_children_empty_errors(self):
        obj = MockValidatableNoChildren(errors=[])
        self.assertTrue(obj._is_valid)

    def test_is_valid_no_children_with_errors(self):
        obj = MockValidatableNoChildren(errors=['err1', 'err2'])
        self.assertFalse(obj._is_valid)

    def test_is_valid_with_children_with_error_on_parent(self):
        child_a = MockValidatableNoChildren()
        child_b = MockValidatableNoChildren()
        obj = MockValidatableWithChildren(child_a, child_b, errors=['err1', 'some err'])
        self.assertFalse(obj._is_valid)

    def test_is_valid_with_children_no_errors_in_a_child(self):
        child_a = MockValidatableNoChildren()
        child_b = MockValidatableNoChildren()
        obj = MockValidatableWithChildren(child_a, child_b)
        self.assertTrue(obj._is_valid)

    def test_is_valid_with_children_no_errors_in_a_child_a_child_is_None(self):
        child_a = MockValidatableNoChildren()
        child_b = None
        obj = MockValidatableWithChildren(child_a, child_b)
        self.assertTrue(obj._is_valid)

    def test_is_valid_with_list_children(self):
        child_a = MockValidatableNoChildren()
        child_b = [
            MockValidatableWithChildren(MockValidatableNoChildren(), MockValidatableNoChildren()),
            MockValidatableNoChildren(),
            None,
            MockValidatableWithChildren(MockValidatableNoChildren(errors=['err1']), MockValidatableNoChildren())
        ]
        obj = MockValidatableWithChildren(child_a, child_b)
        self.assertFalse(obj._is_valid)
