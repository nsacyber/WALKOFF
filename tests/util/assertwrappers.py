
def orderless_list_compare(klass, list1, list2):
    klass.assertEqual(len(list1), len(list2))
    klass.assertEqual(set(list1), set(list2))


def assert_raises_with_error(klass, exception_klass, message, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
        klass.assertFail()
    except Exception as error:
        klass.assertIsInstance(error, exception_klass)
        klass.assertEqual(error.message, message)