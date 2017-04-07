import json


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


def __assert_url_access(klass, app, url, method, status, **kwargs):
    if method.lower() == 'get':
        response = app.get(url, **kwargs)
    elif method.lower() == 'post':
        response = app.post(url, **kwargs)
    else:
        raise ValueError('method must be either get or post')
    klass.assertEqual(response.status_code, 200)
    response = json.loads(response.get_data(as_text=True))
    klass.assertIn('status', response)
    klass.assertEqual(response['status'], status)
    return response


def post_with_status_check(klass, app, url, status, **kwargs):
    return __assert_url_access(klass, app, url, 'post', status, **kwargs)


def get_with_status_check(klass, app, url, status, **kwargs):
    return __assert_url_access(klass, app, url, 'get', status, **kwargs)