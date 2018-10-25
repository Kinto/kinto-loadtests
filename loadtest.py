import os
import uuid

from molotov import global_setup, global_teardown, setup, scenario
from molotov.util import set_var, get_var

# Read configuration from env
SERVER_URL = os.getenv(
    'KINTO_WE_SERVER',
    "https://webextensions-settings.stage.mozaws.net").rstrip('/')

COLLECTIONS = "/v1/buckets/default/collections"

STATUS_URL = "/v1/"
VERSION_URL = "/v1/__version__"


@scenario(100)
async def access_bucket_collection_records(session):
    """Access the list of records."""
    async with session.get(SERVER_URL + STATUS_URL) as r:
        body = await r.json()
        assert 'project_name' in body
