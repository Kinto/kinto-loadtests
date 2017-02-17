import os

from fxa.__main__ import DEFAULT_CLIENT_ID
from fxa.core import Client
from fxa.tests.utils import TestEmailAccount
from fxa.tools.bearer import get_bearer_token
from molotov import global_setup, global_teardown, setup, scenario


# Read configuration from env
SERVER_URL = os.getenv(
    'KINTO_WE_SERVER',
    "https://webextensions-settings.stage.mozaws.net").rstrip('/')

COLLECTIONS = "/v1/buckets/default/collections"

STATUS_URL = "/v1/"
VERSION_URL = "/v1/__version__"

_FXA = {}

@global_setup()
def create_account_and_token(args):
    acct = TestEmailAccount()
    client = Client("https://api.accounts.firefox.com")
    session = client.create_account(
        acct.email,
        'MySecretPassword'
    )
    m = acct.wait_for_email(lambda m: "x-verify-code" in m["headers"])

    if m is None:
        raise RuntimeError("verification email did not arrive")

    session.verify_email_code(m["headers"]["x-verify-code"])
    _FXA['token']= get_bearer_token(
        acct.email,
        'MySecretPassword',
        account_server_url="https://api.accounts.firefox.com/v1",
        oauth_server_url="https://oauth.accounts.firefox.com/v1",
        scopes=['sync:addon_storage'],
        client_id=DEFAULT_CLIENT_ID
    )
    _FXA['acct'] = acct
    _FXA['client'] = client


@global_teardown()
def cleanup_account():
    acct = _FXA['acct']
    client = _FXA['client']
    acct.clear()
    client.destroy_account(acct.email, "MySecretPassword")


@setup()
async def init_test(worker_id, args):
    headers = {"Authorization": "Bearer %s" % _FXA['token']}
    return {'headers': headers}


@scenario(100)
async def access_bucket_collection_records(session):
    """Access the list of records."""
    async with session.get(SERVER_URL + STATUS_URL) as r:
        body = await r.json()
        assert 'user' in body

    async with session.get(SERVER_URL + COLLECTIONS) as r:
        body = await r.json()
        assert "data" in body, "data not found in body"

    requests = []
    for collection in body['data']:
        requests.append({
            "path": COLLECTIONS + "/" + collection['id']
        })
        requests.append({
            "path": COLLECTIONS + "/" + collection['id'] + "/records"
        })


