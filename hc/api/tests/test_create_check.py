import json

from hc.api.models import Channel, Check
from hc.test import BaseTestCase


class CreateCheckTestCase(BaseTestCase):
    URL = "/api/v1/checks/"

    def setUp(self):
        super(CreateCheckTestCase, self).setUp()

    def post(self, data, expected_error=None):
        response = self.client.post(self.URL, json.dumps(data),
                             content_type="application/json")

        if expected_error:
            self.assertEqual(response.status_code, 400)
            ### Assert that the expected error is the response error

            self.assertEqual(response.json()['error'], expected_error)

        return response

    def test_it_works(self):
        response = self.post({
            "api_key": "abc",
            "name": "Foo",
            "tags": "bar,baz",
            "timeout": 3600,
            "grace": 60
        })

        self.assertEqual(response.status_code, 201)

        doc = response.json()
        assert "ping_url" in doc
        self.assertEqual(doc["name"], "Foo")
        self.assertEqual(doc["tags"], "bar,baz")


        ### Assert the expected last_ping and n_pings values

        self.assertEqual(doc["last_ping"], None)
        self.assertEqual(doc["n_pings"], 0)

        self.assertEqual(Check.objects.count(), 1)
        check = Check.objects.get()
        self.assertEqual(check.name, "Foo")
        self.assertEqual(check.tags, "bar,baz")
        self.assertEqual(check.timeout.total_seconds(), 3600)
        self.assertEqual(check.grace.total_seconds(), 60)

    def test_it_accepts_api_key_in_header(self):
        payload = json.dumps({"name": "Foo"})
        ### Make the post request and get the response

        response = self.client.post(self.URL, payload, HTTP_X_API_KEY='abc',
                                content_type="application/json")
        #response = {'status_code': 201} ### This is just a placeholder variable

        self.assertEqual(response.status_code, 201)

    def test_it_handles_missing_request_body(self):
        ### Make the post request with a missing body and get the response
        #response = {'status_code': 400, 'error': "wrong api_key"}
        ### This is just a placeholder variable

        payload = {}
        response = self.client.post(self.URL,payload,HTTP_X_API_KEY='abc',
                                content_type="application/json")
        self.assertEqual(response.status_code, 201)

        self.assertEqual(response.json()["name"], "")


    def test_it_handles_invalid_json(self):
        ### Make the post request with invalid json data type
        URL = "/api/v1/checks/"
        payload = " This is an invalid data type"
        #response = {'status_code': 400, 'error': "could not parse request body"}

        response = self.client.post(URL, payload, HTTP_X_API_KEY='abc',
                                content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "could not parse request body")

    def test_it_rejects_wrong_api_key(self):
        self.post({"api_key": "wrong"},
                  expected_error="wrong api_key")

    def test_it_rejects_non_number_timeout(self):
        self.post({"api_key": "abc", "timeout": "oops"},
                  expected_error="timeout is not a number")

    def test_it_rejects_non_string_name(self):
        self.post({"api_key": "abc", "name": False},
                  expected_error="name is not a string")

    ### Test for the assignment of channels
    def test_channel_assignment(self):
        response = self.post({
            "api_key": "abc",
            "name": "channel_test",
            "tags": "bar,baz",
            "timeout": 3600,
            "grace": 60,
            "channels": "*"
        })
        channels = Channel.objects.filter(user = self.alice)
        for channel in channels:
            print(channel)

    ### Test for the 'timeout is too small' and 'timeout is too large' errors
    def test_timeout_too_small(self):
        response = self.post({
            "api_key": "abc",
            "name": "small",
            "tags": "bar,baz",
            "timeout": 59,
            "grace": 60
        })
        self.assertEqual(response.json()["error"],"timeout is too small")


    def test_timeout_too_large(self):
        response = self.post({
            "api_key": "abc",
            "name": "small",
            "tags": "bar,baz",
            "timeout": 604801,
            "grace": 60
        })
        self.assertEqual(response.json()["error"],"timeout is too large")
