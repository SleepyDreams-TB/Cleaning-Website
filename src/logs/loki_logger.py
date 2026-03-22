import time
import json
import httpx
import os
from typing import cast

LOKI_URL = cast(str, os.getenv("LOKI_URL"))
LOKI_USER = cast(str, os.getenv("LOKI_USER"))
LOKI_KEY = cast(str, os.getenv("LOKI_KEY"))

async def push_to_loki(service: str, event_type: str, payload: dict):
    """Push logs to Loki"""
    body = {
        "streams": [{
            "stream": {
                "service": service,
                "event_type": event_type
            },
            "values": [[
                str(time.time_ns()),
                json.dumps(payload)
            ]]
        }]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LOKI_URL,
                json=body,
                auth=(LOKI_USER, LOKI_KEY)
            )
    except Exception as e:
        print(f"Failed to push to Loki: {e}")