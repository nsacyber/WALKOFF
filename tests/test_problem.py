from unittest import TestCase
from walkoff.server.problem import Problem
import json


class TestProblem(TestCase):

    #examples taken from RFC 7807

    def setUp(self):
        self.title = 'You do not have enough credit.'
        self.detail = 'Your current balance is 30, but that costs 50.'
        self.instance = '/account/12345/msgs/abc'
        self.type_ = 'https://example.com/probs/out-of-credit'
        self.status = 400
        self.expected = {'type': 'about:blank', 'title': self.title, 'detail': self.detail, 'status': self.status}
        self.ext = {'balance': 30, 'accounts': ['/account/12345', '/account/67890']}

    def test_make_response_body(self):
        self.assertEqual(Problem.make_response_body(self.status, self.title, self.detail), json.dumps(self.expected))

    def test_make_response_body_with_instance(self):
        self.expected['instance'] = self.instance
        self.assertEqual(
            Problem.make_response_body(self.status, self.title, self.detail, instance=self.instance),
            json.dumps(self.expected))

    def test_make_response_body_with_type(self):
        status = 404
        self.expected['type'] = self.type_
        self.expected['status'] = status
        self.assertEqual(
            Problem.make_response_body(status, self.title, self.detail, type_=self.type_), json.dumps(self.expected))

    def test_make_response_body_with_ext(self):
        self.expected.update(self.ext)
        self.assertEqual(
            Problem.make_response_body(self.status, self.title, self.detail, ext=self.ext),
            json.dumps(self.expected))

    def test_init(self):
        problem = Problem(self.status, self.title, self.detail, instance=self.instance, type_=self.type_, ext=self.ext)
        self.expected.update(self.ext)
        self.expected.update({'type': self.type_, 'instance': self.instance})
        # For some reason Werkzueg puts the response in a list and as a bytes string in Python 3
        response = json.loads(problem.response[0].decode('utf-8'))
        self.assertDictEqual(response, self.expected)
        self.assertEqual(problem.status_code, self.status)
        self.assertEqual(len(problem.headers), 2)  # Content-Type and Content-Length
        self.assertEqual(problem.content_type, Problem.default_mimetype)
        self.assertEqual(problem.mimetype, Problem.default_mimetype)

    def test_init_with_headers(self):
        problem = Problem(self.status, self.title, self.detail, headers={'x-error': 'something'})
        response = json.loads(problem.response[0].decode('utf-8'))
        self.assertDictEqual(response, self.expected)
        self.assertIn('x-error', problem.headers)