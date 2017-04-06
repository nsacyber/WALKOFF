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


def __assert_url_access(klass, app, url, method, headers, status, data=None, content_type=None):
    if method.lower() == 'get':
        if data is not None:
            if content_type is not None:
                response = app.get(url, headers=headers, data=data, content_type=content_type)
            else:
                response = app.get(url, headers=headers, data=data)
        else:
            response = app.get(url, headers=headers)
    elif method.lower() == 'post':
        if data is not None:
            if content_type is not None:
                response = app.post(url, headers=headers, data=data, content_type=content_type)
            else:
                response = app.post(url, headers=headers, data=data)
        else:
            response = app.post(url, headers=headers)
    else:
        raise NameError('method must be either get or post')
    klass.assertEqual(response.status_code, 200)
    response = json.loads(response.get_data(as_text=True))
    klass.assertIn('status', response)
    klass.assertEqual(response['status'], status)
    return response


def assert_post_status(klass, app, url, headers, status, data=None, content_type=None):
    return __assert_url_access(klass, app, url, 'post', headers, status, data, content_type)


def assert_get_status(klass, app, url, headers, status, data=None, content_type=None):
    return __assert_url_access(klass, app, url, 'get', headers, status, data, content_type)