import warnings
from functools import wraps

def orderless_list_compare(cls, list1, list2):
    cls.assertEqual(len(list1), len(list2))
    cls.assertEqual(set(list1), set(list2))


def assert_raises_with_error(cls, exception_cls, message, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
        cls.assertFail()
    except Exception as error:
        cls.assertIsInstance(error, exception_cls)
        cls.assertEqual(error.message, message)
