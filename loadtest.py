import os

from molotov import setup, scenario


# Read configuration from env
SERVER_URL = os.getenv(
    'URL_KINTO_SERVER',
    "https://webextensions-settings.stage.mozaws.net").rstrip('/')

#FXA_BEARER_TOKEN = os.getenv("FXA_BEARER_TOKEN")
FXA_BEARER_TOKEN = "b188fdd9f7a3266fbbe6e28754f7f1fe7deb3b0ca1b61fae7bfc7c55c2e279cd"
if not FXA_BEARER_TOKEN:
    raise ValueError("Please define FXA_BEARER_TOKEN env variable.")

CONNECTIONS = {}

COLLECTIONS = "/v1/buckets/default/collections"

STATUS_URL = "/v1/"
VERSION_URL = "/v1/__version__"

'''
http -v GET "${SERVER_URL}/buckets/default/collections" Authorization:"Bearer ${OAUTH_BEARER_TOKEN}"
'''

@setup()
async def init_test(args):
    headers = {"Authorization": "Bearer %s" % FXA_BEARER_TOKEN}
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

    batch_data = {
        "defaults": {
            "method": "GET"
        },
        "requests": requests
    }

    async with session.post(SERVER_URL + '/v1/batch/', json=batch_data) as r:
        body = await r.json()
        print(body)
