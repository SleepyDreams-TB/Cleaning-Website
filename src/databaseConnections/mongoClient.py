from pymongo import MongoClient
from typing import cast
import os

MONGO_URI = cast(str, os.getenv("MONGO_URI"))
_client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
_db = _client["kingburgerstore_db"]

def get_collection(collection_name: str):
    return _db[collection_name]