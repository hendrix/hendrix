import unittest

from twisted.web.resource import getChildForRequest, NoResource
from twisted.web.test.requesthelper import DummyRequest

try:
    from unittest import mock
except ImportError:
    import mock

from hendrix.facilities.resources import HendrixResource, NamedResource, WSGIResource


class TestHendrixResource(unittest.TestCase):

    def setUp(self):
        path = '/path/to/child/'
        self.res = NamedResource(path)
        self.hr = HendrixResource(None, None, None)
        self.hr.putNamedChild(self.res)

    def test_putNamedChild_success(self):
        with mock.patch('hendrix.facilities.resources.WSGIResource') as wsgi:
            request = DummyRequest(['path', 'to', 'child'])
            actual_res = getChildForRequest(self.hr, request)
            self.assertEqual(self.res, actual_res)

    def test_putNamedChild_very_wrong_request(self):
        "check that requests outside of the children go to the WSGIResoure"
        with mock.patch('hendrix.facilities.resources.WSGIResource') as wsgi:
            request = DummyRequest(['very', 'wrong', 'uri'])
            actual_res = getChildForRequest(self.hr, request)
            self.assertIsInstance(actual_res, WSGIResource)

    def test_putNamedChild_sort_of_wrong_request(self):
        "requests to incorrect subpaths go to NoResource"
        with mock.patch('hendrix.facilities.resources.WSGIResource') as wsgi:
            request = DummyRequest(['path', 'to', 'wrong'])
            actual_res = getChildForRequest(self.hr, request)
            self.assertIsInstance(actual_res, NoResource)

    def test_putNamedChild_duplicate(self):
        "check that duplicate resources work"
        with mock.patch('hendrix.facilities.resources.WSGIResource') as wsgi:
            request = DummyRequest(['path', 'to', 'child'])
            actual_res = getChildForRequest(self.hr, request)
            self.assertEqual(self.res, actual_res)  # Before duplicate

            duplicate = NamedResource(self.res.namespace)
            self.hr.putNamedChild(duplicate)
            request = DummyRequest(['path', 'to', 'child'])
            actual_duplicate_res = getChildForRequest(self.hr, request)
            self.assertEqual(duplicate, actual_duplicate_res)  # After duplicate
