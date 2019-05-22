import unittest
import unittest.mock

import os
import json

import service

class MockRedis(object):

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.channel = None

        self.messages = []

    def publish(self, channel, message):

        self.channel = channel
        self.messages.append(message)

class TestService(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch.dict(os.environ, {
        "REDIS_HOST": "most.com",
        "REDIS_PORT": "667",
        "REDIS_CHANNEL": "stuff"
    })
    @unittest.mock.patch("redis.StrictRedis", MockRedis)
    @unittest.mock.patch("os.path.exists", unittest.mock.MagicMock(return_value=True))
    @unittest.mock.patch("pykube.HTTPClient", unittest.mock.MagicMock)
    @unittest.mock.patch("pykube.KubeConfig.from_service_account", unittest.mock.MagicMock)
    def setUp(self):

        self.app = service.app()
        self.api = self.app.test_client()

    @unittest.mock.patch.dict(os.environ, {
        "REDIS_HOST": "most.com",
        "REDIS_PORT": "667",
        "REDIS_CHANNEL": "stuff"
    })
    @unittest.mock.patch("redis.StrictRedis", MockRedis)
    @unittest.mock.patch("os.path.exists")
    @unittest.mock.patch("pykube.KubeConfig.from_file")
    @unittest.mock.patch("pykube.KubeConfig.from_service_account")
    @unittest.mock.patch("pykube.KubeConfig.from_url")
    @unittest.mock.patch("pykube.HTTPClient", unittest.mock.MagicMock)
    def test_app(self, mock_url, mock_account, mock_file, mock_exists):

        mock_exists.return_value = True
        app = service.app()

        self.assertEqual(app.redis.host, "most.com")
        self.assertEqual(app.redis.port, 667)
        self.assertEqual(app.channel, "stuff")

        mock_exists.assert_called_once_with("/var/run/secrets/kubernetes.io/serviceaccount/token")
        mock_account.assert_called_once()

        mock_exists.return_value = False
        app = service.app()

        mock_url.assert_called_once_with("http://host.docker.internal:7580")

    def test_health(self):

        self.assertEqual(self.api.get("/health").json, {"message": "OK"})

    @unittest.mock.patch("pykube.Node.objects")
    @unittest.mock.patch("service.time.time")
    def test_Speak(self, mock_time, mock_nodes):

        mock_node_a = unittest.mock.MagicMock()
        mock_node_a.obj = {
            "metadata": {
                "name": "a"
            }
        }
        mock_node_b = unittest.mock.MagicMock()
        mock_node_b.obj = {
            "metadata": {
                "name": "b"
            }
        }
        mock_nodes.return_value.filter.return_value = [mock_node_b, mock_node_a]

        response = self.api.options("/speak")
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json, {
            "fields": [
                {
                    "name": "text"
                },
                {
                    "name": "language",
                    "options": [
                        "en-AU",
                        "en-CA",
                        "en-GH",
                        "en-GB",
                        "en-IN",
                        "en-IE",
                        "en-KE",
                        "en-NZ",
                        "en-NG",
                        "en-PH",
                        "en-SG",
                        "en-ZA",
                        "en-TZ",
                        "en-US"
                    ],
                    "labels": {
                        "en-AU": "English (Australia)",
                        "en-CA": "English (Canada)",
                        "en-GH": "English (Ghana)",
                        "en-GB": "English (United Kingdom)",
                        "en-IN": "English (India)",
                        "en-IE": "English (Ireland)",
                        "en-KE": "English (Kenya)",
                        "en-NZ": "English (New Zealand)",
                        "en-NG": "English (Nigeria)",
                        "en-PH": "English (Philippines)",
                        "en-SG": "English (Singapore)",
                        "en-ZA": "English (South Africa)",
                        "en-TZ": "English (Tanzania)",
                        "en-US": "English (United States)"
                    },
                    "default": "en-US",
                    "style": "select"
                },
                {
                    "name": "node",
                    "options": [
                        "",
                        "a",
                        "b"
                    ],
                    "labels": {
                        "": "all",
                        "a": "a",
                        "b": "b"
                    },
                    "default": "",
                    "optional": True
                }
            ]
        })

        mock_nodes.assert_called_once_with(self.app.kube)
        mock_nodes.return_value.filter.assert_called_once_with(selector={"speech.nandy.io/speakers": "enabled"})

        response = self.api.options("/speak", json={"speak": {"node": "c"}})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json, {
            "fields": [
                {
                    "name": "text",
                    "errors": ["missing value"]
                },
                {
                    "name": "language",
                    "options": [
                        "en-AU",
                        "en-CA",
                        "en-GH",
                        "en-GB",
                        "en-IN",
                        "en-IE",
                        "en-KE",
                        "en-NZ",
                        "en-NG",
                        "en-PH",
                        "en-SG",
                        "en-ZA",
                        "en-TZ",
                        "en-US"
                    ],
                    "labels": {
                        "en-AU": "English (Australia)",
                        "en-CA": "English (Canada)",
                        "en-GH": "English (Ghana)",
                        "en-GB": "English (United Kingdom)",
                        "en-IN": "English (India)",
                        "en-IE": "English (Ireland)",
                        "en-KE": "English (Kenya)",
                        "en-NZ": "English (New Zealand)",
                        "en-NG": "English (Nigeria)",
                        "en-PH": "English (Philippines)",
                        "en-SG": "English (Singapore)",
                        "en-ZA": "English (South Africa)",
                        "en-TZ": "English (Tanzania)",
                        "en-US": "English (United States)"
                    },
                    "default": "en-US",
                    "style": "select",
                    "value": "en-US"
                },
                {
                    "name": "node",
                    "options": [
                        "",
                        "a",
                        "b"
                    ],
                    "labels": {
                        "": "all",
                        "a": "a",
                        "b": "b"
                    },
                    "default": "",
                    "optional": True,
                    "value": "c",
                    "errors": ["invalid value 'c'"]
                }
            ],
            "errors": []
        })

        response = self.api.post("/speak")
        self.assertEqual(response.status_code, 400, response.json)
        self.assertEqual(response.json["errors"], ["missing speak"])

        response = self.api.post("/speak", json={"speak": {"node": "c"}})
        self.assertEqual(response.status_code, 400, response.json)
        self.assertEqual(response.json, {
            "fields": [
                {
                    "name": "text",
                    "errors": ["missing value"]
                },
                {
                    "name": "language",
                    "options": [
                        "en-AU",
                        "en-CA",
                        "en-GH",
                        "en-GB",
                        "en-IN",
                        "en-IE",
                        "en-KE",
                        "en-NZ",
                        "en-NG",
                        "en-PH",
                        "en-SG",
                        "en-ZA",
                        "en-TZ",
                        "en-US"
                    ],
                    "labels": {
                        "en-AU": "English (Australia)",
                        "en-CA": "English (Canada)",
                        "en-GH": "English (Ghana)",
                        "en-GB": "English (United Kingdom)",
                        "en-IN": "English (India)",
                        "en-IE": "English (Ireland)",
                        "en-KE": "English (Kenya)",
                        "en-NZ": "English (New Zealand)",
                        "en-NG": "English (Nigeria)",
                        "en-PH": "English (Philippines)",
                        "en-SG": "English (Singapore)",
                        "en-ZA": "English (South Africa)",
                        "en-TZ": "English (Tanzania)",
                        "en-US": "English (United States)"
                    },
                    "default": "en-US",
                    "style": "select",
                    "value": "en-US"
                },
                {
                    "name": "node",
                    "options": [
                        "",
                        "a",
                        "b"
                    ],
                    "labels": {
                        "": "all",
                        "a": "a",
                        "b": "b"
                    },
                    "default": "",
                    "optional": True,
                    "value": "c",
                    "errors": ["invalid value 'c'"]
                }
            ],
            "errors": []
        })

        mock_time.return_value = 7

        response = self.api.post("/speak", json={
            "speak": {
                "text": "hi",
                "language": "en-AU"
            }
        })
        self.assertEqual(response.status_code, 202, response.json)
        self.assertEqual(response.json, {
            "message": {
                "timestamp": 7,
                "text": "hi",
                "language": "en-AU"
            }
        })
        self.assertEqual(self.app.redis.channel, "stuff")
        self.assertEqual(json.loads(self.app.redis.messages[0]), {
            "timestamp": 7,
            "text": "hi",
            "language": "en-AU"
        })

        response = self.api.post("/speak", json={
            "speak": {
                "text": "hi",
                "language": "en-AU",
                "node": "b"
            }
        })
        self.assertEqual(response.status_code, 202, response.json)
        self.assertEqual(response.json, {
            "message": {
                "timestamp": 7,
                "text": "hi",
                "language": "en-AU",
                "node": "b"
            }
        })
        self.assertEqual(self.app.redis.channel, "stuff")
        self.assertEqual(json.loads(self.app.redis.messages[1]), {
            "timestamp": 7,
            "text": "hi",
            "language": "en-AU",
            "node": "b"
        })
