import os
import uuid

from fxa.__main__ import DEFAULT_CLIENT_ID
from fxa.core import Client
from fxa.tests.utils import TestEmailAccount
from fxa.tools.bearer import get_bearer_token
from molotov import teardown_session, setup, scenario


# Read configuration from env
SERVER_URL = os.getenv(
    'KINTO_WE_SERVER',
    "https://webextensions-settings.stage.mozaws.net").rstrip('/')

BUCKET = "/v1/buckets/default"
COLLECTIONS = BUCKET + "/collections"

STATUS_URL = "/v1/"
VERSION_URL = "/v1/__version__"

_FXA_BY_WORKER_ID = {}

async def json_or_error(r):
    if r.content_type != 'application/json':
        text = await r.text()
        raise ValueError("response was not JSON: {}".format(text))

    return await r.json()


@setup()
async def create_account_and_token(worker_id, args):
    acct = TestEmailAccount()
    passwd = str(uuid.uuid4())
    client = Client("https://api.accounts.firefox.com")
    session = client.create_account(
        acct.email,
        passwd
    )
    m = acct.wait_for_email(lambda m: "x-verify-code" in m["headers"])

    if m is None:
        raise RuntimeError("verification email did not arrive")

    session.verify_email_code(m["headers"]["x-verify-code"])
    fxa = {}
    fxa['token']= get_bearer_token(
        acct.email,
        passwd,
        account_server_url="https://api.accounts.firefox.com/v1",
        oauth_server_url="https://oauth.accounts.firefox.com/v1",
        scopes=['sync:addon_storage'],
        client_id=DEFAULT_CLIENT_ID
    )
    fxa['acct'] = acct
    fxa['passwd'] = passwd
    fxa['client'] = client
    _FXA_BY_WORKER_ID[worker_id] = fxa

    headers = {"Authorization": "Bearer %s" % fxa['token'], "Content-type": "application/json;charset=utf8"}
    return {'headers': headers}


@teardown_session()
async def cleanup_account(worker_id, _session):
    fxa = _FXA_BY_WORKER_ID[worker_id]
    acct = fxa['acct']
    client = fxa['client']
    passwd = fxa['passwd']
    acct.clear()
    client.destroy_account(acct.email, passwd)


@scenario(75)
async def access_bucket_collection_records(session):
    """Access the list of records."""
    async with session.get(SERVER_URL + STATUS_URL) as r:
        body = await r.json()
        assert 'user' in body

    async with session.get(SERVER_URL + COLLECTIONS) as r:
        body = await json_or_error(r)
        if "data" not in body:
            if "error" in body:
                raise ValueError("request failed: {} {} ({}, {}, {})".format(
                    body.get('errno'), body.get('code'),
                    body.get('error'), body.get('message'), body.get('info')))
            raise ValueError("data not found in body: {}".format(body.keys()))

    requests = []
    for collection in body['data']:
        requests.append({
            "path": COLLECTIONS + "/" + collection['id']
        })
        requests.append({
            "path": COLLECTIONS + "/" + collection['id'] + "/records"
        })


@scenario(25)
async def create_records(session):
    payload = '{"data": {"payload": {"encrypted": "%s"}}}' % str(uuid.uuid4())
    # headers = {"Authorization": "Bearer %s" % _FXA['token'], "Content-type": "application/json;charset=utf8"}
    async with session.post(SERVER_URL + COLLECTIONS + '/qa_collection/records', data=payload) as resp:
        assert resp.status == 201, "creating failed: {}".format(resp.status)


@scenario(1)
async def wipe_server(session):
    async with session.delete(SERVER_URL + BUCKET) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise ValueError("deleting failed: {} {}".format(resp.status, text))
