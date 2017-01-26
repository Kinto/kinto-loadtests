import json
import os
import uuid

from ailoads.fmwk import scenario, requests

URL_SERVER = os.getenv('URL_KINTO_SERVER',
                       "https://kinto.stage.mozaws.net/v1")
TIMEOUT = 30

_CONNECTIONS = {}


def get_connection(id=None):
    if id is None or id not in _CONNECTIONS:
        id = uuid.uuid4().hex
        conn = KintoConnection(id)
        _CONNECTIONS[id] = conn

    return _CONNECTIONS[id]


class KintoConnection(object):

    def __init__(self, id):
        self.id = id
        self.timeout = TIMEOUT

    def post(self, endpoint, data):
        return requests.post(
            URL_SERVER + endpoint,
            data=json.dumps(data),
            timeout=self.timeout)

    def get(self, endpoint):
        return requests.get(
            URL_SERVER + endpoint,
            timeout=self.timeout)

    def delete(self, endpoint):
        return requests.delete(
            URL_SERVER + endpoint,
            timeout=self.timeout)


@scenario(1)
def demo_test():
    conn = get_connection('demo_connection')
    resp = conn.get('/')
    # body = resp.json()
    # assert "data" in body, "data not found in body"
    resp.raise_for_status()
