import mock
import unittest

from werkzeug.routing import Map, Rule
from werkzeug.test import Client
from werkzeug.wrappers import Response, BaseResponse

from lymph.testing import WebServiceTestCase
from lymph.web.interfaces import WebServiceInterface
from lymph.web.handlers import RequestHandler
from lymph.web.routing import HandledRule


class RuleHandler(RequestHandler):
    def get(self):
        return Response("Rule Handler")


class HandledRuleHandler(RequestHandler):
    def get(self):
        return Response("Handled Rule Handler")


class Web(WebServiceInterface):
    url_map = Map([
        Rule("/test/", endpoint="test"),
        Rule("/foo/", endpoint=RuleHandler),
        HandledRule("/bar/", endpoint="bar", handler=HandledRuleHandler),
        Rule("/fail/", endpoint="fail"),
        Rule("/fail-wrong-endpoint/", endpoint=42),
    ])

    def test(self, request):
        return Response("method test")


class WebIntegrationTest(WebServiceTestCase):

    service_class = Web

    def test_dispatch_rule_with_string_endpoint(self):
        response = self.client.get("/test/")
        self.assertEqual(response.data.decode("utf8"), "method test")
        self.assertEqual(response.status_code, 200)

    def test_dispatch_rule_with_callable_endpoint(self):
        response = self.client.get("/foo/")
        self.assertEqual(response.data.decode("utf8"), "Rule Handler")
        self.assertEqual(response.status_code, 200)

    def test_dispatch_handled_rule(self):
        response = self.client.get("/bar/")
        self.assertEqual(response.data.decode("utf8"), "Handled Rule Handler")
        self.assertEqual(response.status_code, 200)

    def test_dispatch_failing_rule_to_500(self):
        response = self.client.get("/fail/")
        self.assertEqual(response.data.decode("utf8"), "")
        self.assertEqual(response.status_code, 500)

    def test_dispatch_failing_endpoint_to_500(self):
        response = self.client.get("/fail-wrong-endpoint/")
        self.assertEqual(response.data.decode("utf8"), "")
        self.assertEqual(response.status_code, 500)
