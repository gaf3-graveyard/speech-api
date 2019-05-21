import os
import time
import json
import yaml

import redis
import flask
import flask_restful
import opengui
import pykube


def app():

    app = flask.Flask("nandy-io-speech-api")

    app.redis = redis.StrictRedis(host=os.environ['REDIS_HOST'], port=int(os.environ['REDIS_PORT']))
    app.channel = os.environ['REDIS_CHANNEL']

    if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token"):
        app.kube = pykube.HTTPClient(pykube.KubeConfig.from_service_account())
    else:
        app.kube = pykube.HTTPClient(pykube.KubeConfig.from_url("http://host.docker.internal:7580"))

    api = flask_restful.Api(app)

    api.add_resource(Health, '/health')
    api.add_resource(Speak, '/speak')

    return app


class Health(flask_restful.Resource):
    def get(self):
        return {"message": "OK"}


class Speak(flask_restful.Resource):

    name = "speak"

    def fields(self, values=None):

        fields = opengui.Fields(values, fields=[
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
                    ""
                ],
                "labels": {
                    "": "all"
                },
                "default": "",
                "optional": True
            }
        ])

        for node in pykube.Node.objects(flask.current_app.kube).filter(selector={"speech.nandy.io/speakers": "enabled"}):
            fields["node"].options.append(node.obj["metadata"]["name"])
            fields["node"].labels[node.obj["metadata"]["name"]] = node.obj["metadata"]["name"]

        fields["node"].options.sort()

        return fields

    def options(self):

        values = flask.request.json[self.name] if flask.request.json and self.name in flask.request.json else None

        fields = self.fields(values)

        if values and not fields.validate():
            return {"fields": fields.to_list(), "errors": fields.errors}
        else:
            return {"fields": fields.to_list()}

    def post(self):

        if not flask.request.json or self.name not in flask.request.json:
            return {"errors": ["missing %s" % self.name]}, 400

        fields = self.fields(flask.request.json[self.name])

        if not fields.validate():
            return {"fields": fields.to_list(), "errors": fields.errors}, 400

        message = {
            "timestamp": time.time(),
            "text": fields["text"].value,
            "language": fields["language"].value
        }

        if fields["node"].value:
            message["node"] = fields["node"].value

        flask.current_app.redis.publish(flask.current_app.channel, json.dumps(message))

        return {"message": message}, 202
