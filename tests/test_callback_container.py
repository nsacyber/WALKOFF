from unittest import TestCase

from interfaces.disatchers import CallbackContainer


def func(): pass


def func2(): pass


class TestCallbackContainer(TestCase):
    def setUp(self):
        self.callbackcontainer = CallbackContainer()

    def test_init_default(self):
        self.assertSetEqual(self.callbackcontainer.strong, set())
        self.assertEqual(len(self.callbackcontainer.weak), 0)

    def test_init_with_weak(self):
        self.callbackcontainer = CallbackContainer(weak=(func, func2))
        self.assertSetEqual(self.callbackcontainer.strong, set())
        self.assertEqual(len(self.callbackcontainer.weak), 2)

    def test_init_with_strong(self):
        self.callbackcontainer = CallbackContainer(strong=(func, func2))
        self.assertSetEqual(self.callbackcontainer.strong, {func, func2})
        self.assertEqual(len(self.callbackcontainer.weak), 0)

    def test_register_strong(self):
        self.callbackcontainer.register(func, weak=False)
        self.assertSetEqual(self.callbackcontainer.strong, {func})

    def test_register_weak(self):
        self.callbackcontainer.register(func)
        self.assertEqual(len(self.callbackcontainer.weak), 1)

    def test_iteration(self):
        self.callbackcontainer.register(func)
        self.callbackcontainer.register(func, weak=False)
        self.callbackcontainer.register(func2)
        self.callbackcontainer.register(func2, weak=False)
        funcs = [x for x in self.callbackcontainer]
        self.assertEqual(len(funcs), 4)

    def test_iter_strong_none_in_strong(self):
        self.callbackcontainer.register(func)
        self.assertListEqual(list(self.callbackcontainer.iter_strong()), [])

    def test_iter_strong(self):
        self.callbackcontainer.register(func, weak=False)
        self.callbackcontainer.register(func2, weak=False)
        self.assertSetEqual(set(self.callbackcontainer.iter_strong()), {func, func2})

    def test_iter_weak_none_in_weak(self):
        self.callbackcontainer.register(func, weak=False)
        self.assertListEqual(list(self.callbackcontainer.iter_weak()), [])

    def test_iter_weak(self):
        self.callbackcontainer.register(func)
        self.callbackcontainer.register(func2)
        self.assertEqual(len(list(self.callbackcontainer.iter_weak())), 2)

    def test_is_registered_empty(self):
        self.assertFalse(self.callbackcontainer.is_registered(func))

    def test_is_registered_not_registered(self):
        self.callbackcontainer.register(func2)
        self.assertFalse(self.callbackcontainer.is_registered(func))

    def test_is_registered_is_registered_weak(self):
        self.callbackcontainer.register(func)
        self.assertTrue(self.callbackcontainer.is_registered(func))

    def test_is_registered_is_registered_strong(self):
        self.callbackcontainer.register(func, weak=False)
        self.assertTrue(self.callbackcontainer.is_registered(func))
