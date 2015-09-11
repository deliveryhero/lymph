from werkzeug.exceptions import NotFound, MethodNotAllowed
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response

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


class CustomNotFound(NotFound):
    def __init__(self):
        response = Response("never-gonna-match-you-down", status=404)
        super(CustomNotFound, self).__init__(response=response)


class CustomMethodNotAllowed(MethodNotAllowed):
    def get_body(self, *args, **kwargs):
        return "never-gonna-run-around-or-post-you"


class Web(WebServiceInterface):
    url_map = Map([
        Rule("/test/", endpoint="test"),
        Rule("/foo/", endpoint=RuleHandler, methods=['get']),
        Rule("/baz/", endpoint=RuleHandler),
        HandledRule("/bar/", endpoint="bar", handler=HandledRuleHandler),
        Rule("/fail/", endpoint="fail"),
        Rule("/fail-wrong-endpoint/", endpoint=42),
    ])

    def test(self, request):
        return Response("method test")


class CustomErrorHandlingWeb(Web):
    NotFound = CustomNotFound
    MethodNotAllowed = CustomMethodNotAllowed


class WebIntegrationTest(WebServiceTestCase):

    service_class = Web

    def test_dispatch_rule_with_string_endpoint(self):
        response = self.client.get("/test/")
        self.assertEqual(response.data.decode("utf8"), "method test")
        self.assertEqual(response.status_code, 200)

    def test_dispatch_rule_with_no_trailing_slash(self):
        response = self.client.get("/test", follow_redirects=True)
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

    def test_dispatch_not_found(self):
        response = self.client.get("/never-gonna-match-me-up/")
        self.assertEqual(response.status_code, 404)

    def test_dispatch_methond_not_allowed(self):
        response = self.client.post("/bar/")
        self.assertEqual(response.status_code, 405)

        response = self.client.post("/foo/")
        self.assertEqual(response.status_code, 405)

        response = self.client.post("/baz/")
        self.assertEqual(response.status_code, 405)


class CustomErrorHandlingWebIntegrationTest(WebIntegrationTest):

    service_class = CustomErrorHandlingWeb

    def test_dispatch_not_found(self):
        response = self.client.get("/never-gonna-match-me-up/")
        self.assertEqual(response.data.decode("utf8"), "never-gonna-match-you-down")
        self.assertEqual(response.status_code, 404)

    def test_dispatch_methond_not_allowed(self):
        response = self.client.post("/bar/")
        self.assertEqual(response.data.decode("utf8"), "never-gonna-run-around-or-post-you")
        self.assertEqual(response.status_code, 405)

        response = self.client.post("/foo/")
        self.assertEqual(response.data.decode("utf8"), "never-gonna-run-around-or-post-you")
        self.assertEqual(response.status_code, 405)

        response = self.client.post("/baz/")
        self.assertEqual(response.data.decode("utf8"), "never-gonna-run-around-or-post-you")
        self.assertEqual(response.status_code, 405)
