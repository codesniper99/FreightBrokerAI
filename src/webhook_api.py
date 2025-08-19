import json
import re
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Request

from .db_client import fetch_recent_loads, find_closest_by_weight

app = FastAPI(title="Webhook Receiver")
INCOMING_TOKEN = "shared_Secret_key"
@app.get("/health")
def health() -> Dict[str, str]:
    return {"ok": "true"}

@app.post("/webhook")
async def receive_webhook(request : Request,
                          authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    # if INCOMING_TOKEN:
    #     expected = f"Bearer {INCOMING_TOKEN}"
    #     if authorization != expected:
    #         raise HTTPException(status_code=401, detail="Unauthorized")

    # # Read the body ONCE and parse
    # ct = (request.headers.get("content-type") or "").lower()
    # raw = await request.body()       # <-- await
    # body: Any

    # if ct.startswith("application/json"):
    #     try:
    #         body = json.loads(raw)   # parse ourselves so we only read once
    #     except json.JSONDecodeError:
    #         body = raw.decode("utf-8", errors="ignore")
    # else:
    #     # For non-JSON bodies, return text
    #     body = raw.decode("utf-8", errors="ignore")

    # print("Incoming Webhook")
    # print("Headers:", dict(request.headers))
    # print("Parsed body:", body)

    # # Return ONLY JSON-serializable types (dict/list/str/int/float/bool/None)
    # return {"status": "ok", "received": body}
    if INCOMING_TOKEN:
        expected = f"Bearer {INCOMING_TOKEN}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # read body
    body = await request.json()

    # naive weight extraction e.g., "10kg"
    text = str(body)
    m = re.search(r"(\d+)\s*kg", text, flags=re.I)
    closest = find_closest_by_weight(int(m.group(1))) if m else fetch_recent_loads(5)

    return {
        "ok": True,
        "echo": body,
        "suggested_loads": closest
    }

@app.get("/loads")
def loads(limit: int = 10):
    return {"loads": fetch_recent_loads(limit)}
    