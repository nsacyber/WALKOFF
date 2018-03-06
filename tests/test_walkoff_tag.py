from unittest import TestCase

from walkoff.appgateway.decorators import action, condition
from walkoff.appgateway.walkofftag import WalkoffTag


class TestWalkoffTag(TestCase):

    def test_tag(self):
        for tag in WalkoffTag:
            def foo():
                pass

            tag.tag(foo)
            self.assertTrue(tag.is_tagged(foo))
            for other_tag in (other_tag for other_tag in WalkoffTag if other_tag != tag):
                self.assertFalse(other_tag.is_tagged(foo))

    def test_get_tags_no_tags(self):
        def foo(): pass

        self.assertSetEqual(WalkoffTag.get_tags(foo), set())

    def test_get_tags(self):
        @action
        @condition
        def foo(): pass

        self.assertSetEqual(WalkoffTag.get_tags(foo), {WalkoffTag.action, WalkoffTag.condition})
