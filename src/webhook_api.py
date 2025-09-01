import datetime
import json
import os, httpx
import time

import uuid
from pathlib import Path
import re
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import psycopg

from src.analytics import log_event

from .db_client import fetch_negotiations_by_session, fetch_recent_loads, find_closest_by_weight, insert_negotiation, search_loads

class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        self.ms = None
        return self
    def __exit__(self, exc_type, exc, tb):
        self.ms = int((time.perf_counter() - self.start) * 1000)
    def elapsed(self):
        return int((time.perf_counter() - self.start) * 1000)
    

DIST_DIR = Path(__file__).resolve().parents[1] / "frontend" / "dist"
SESS: Dict[str, Dict[str, Any]] = {}
JOBS: Dict[str, Dict[str, Any]] = {}
JOBS["job-id-1234"] = {}
JOBS["job_12345"] = {}
NEGOTIATION_WEBHOOK_URL = os.environ.get("NEGOTIATION_WEBHOOK_URL")
NEGOTIATION_API_KEY = os.environ.get("NEGOTIATION_API_KEY")  # secret stays on server

app = FastAPI(title="Webhook Receiver")
app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")


@app.get("/")
def index():
    return FileResponse(DIST_DIR / "index.html")
    
INCOMING_TOKEN = "shared_Secret_key"
FMCSA_API_KEY = os.environ.get("FMCSA_API_KEY")
API_KEY  = os.getenv("API_KEY")
@app.get("/health")
def health() -> Dict[str, str]:
    return {"ok": "true"}

@app.post("/mc_key/{mc_key}")
async def fetch_carrier_information(
    mc_key: str,
    authorization: Optional[str] = Header(None),
):
    # check auth
    if INCOMING_TOKEN:
        expected = f"Bearer {INCOMING_TOKEN}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # call FMCSA
    url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/{mc_key}?webKey={FMCSA_API_KEY}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        raw = r.json()

    content = (raw or {}).get("content") or {}
    carrier = content.get("carrier") or {}

    status_code = (carrier.get("statusCode") or "").upper()
    allowed = str(carrier.get("allowedToOperate") or "").upper() == "Y"
    eligible = status_code == "A" and allowed

    return {
        "mc": mc_key,
        "legal_name": carrier.get("legalName"),
        "dba_name": carrier.get("dbaName"),
        "status": status_code,
        "eligible": eligible,
        "city": carrier.get("phyCity"),
        "state": carrier.get("phyState"),
    }

@app.post("/start_clean")
async def start_clean(request: Request):
    body = await request.json()
    user_message = body.get("user_message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Missing user_message")
    
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    if not WEBHOOK_URL:
        raise  HTTPException(status_code=500, detail="WEBHOOK_URL not set")
    
    # 1. Generate job_id
    job_id = str(uuid.uuid4())

    # 2. Store job as pending
    JOBS[job_id] = {
        "status": "pending",
        "started_at": datetime.datetime.now().isoformat(),
        "user_message": user_message,
        "result": None,
    }
    
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {INCOMING_TOKEN}"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    # 3. Forward request to HappyRobot
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                WEBHOOK_URL,
                json={"text": user_message, "job_id": job_id},  # include job_id!
                headers=headers
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding to HappyRobot: {e}")

    # 4. Return job_id so frontend can poll
    return {"ok": True, "job_id": job_id}


@app.get("/result/{job_id}")
async def get_result(job_id: str, authorization: Optional[str] = Header(None)):
    expected = f"Bearer {INCOMING_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    # print(f"Found job for {job_id} is {job}")
    return {
        "ok": True,
        "status": job["status"],
        "echo": job.get("echo"),
        "suggested_loads": job.get("suggested_loads"),
    }

@app.post("/webhook")
async def receive_webhook(request : Request,
                          authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if INCOMING_TOKEN:
        expected = f"Bearer {INCOMING_TOKEN}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")
    
    
    with Timer() as t: # type: ignore
        body = await request.json()

        # === Structured agent request (preferred) ===
        # print("body is")
        # print(body)
        job_id = body.get("job_id")
        if not job_id:
            raise HTTPException(status_code=400, detail="Missing job_id")
        loads: list = []
        echo = body.get("echo")

        if isinstance(body, dict) and any(k in body for k in (
            "origin", "destination", "weight_kg", "miles", "rate_min", "rate_max"
        )):
            loads = search_loads(
                origin=body.get("origin") or None,
                destination=body.get("destination") or None,
                weight_kg=body.get("weight_kg") or None,
                miles=body.get("miles") or None,
                rate_min=body.get("rate_min") if body.get("rate_min") not in ("", None) else None,
                rate_max=body.get("rate_max") if body.get("rate_max") not in ("", None) else None,
                limit=body.get("limit") or 10,
            )
            print(f"Time is {t.elapsed()}")

            log_event(
                source="webhook",
                name="structured_query",
                status="ok",
                duration_ms=t.elapsed(),
                route="/webhook/",
                payload={
                    "origin": body.get("origin"),
                    "destination": body.get("destination"),
                    "weight_kg": body.get("weight_kg"),
                    "miles": body.get("miles"),
                    "rate_min": body.get("rate_min"),
                    "rate_max": body.get("rate_max"),
                    "limit": body.get("limit"),
                }
            )
        else:
            text = str(body)
            m = re.search(r"(\d+)\s*kg", text, flags=re.I)
            if m:
                loads = [find_closest_by_weight(int(m.group(1)))]
                log_event(
                source="webhook",
                name="fallback_text_query",
                status="ok",
                duration_ms=t.elapsed(),
                route="/webhook",
                payload={
                    "raw_text": text,
                    "weight_guess": int(m.group(1)) if m else None,
                    "strategy": "closest_by_weight" if m else "recent_loads",
                }
            )
            else:
                loads = fetch_recent_loads(5)
            
    
    # naive weight extraction e.g., "10kg"
    # text = str(body)
    # m = re.search(r"(\d+)\s*kg", text, flags=re.I)
    # closest = find_closest_by_weight(int(m.group(1))) if m else fetch_recent_loads(5)
    
    JOBS[job_id]["status"] = "done"
    JOBS[job_id]["suggested_loads"] = loads
    JOBS[job_id]["echo"] = body.get("echo")
    
    return {
        "ok": True,
        "echo": body,
        "suggested_loads": loads
    }

@app.get("/loads")
def loads(limit: int = 10):
    return {"loads": fetch_recent_loads(limit)}

# Start negotiation
@app.post("/negotiate/start")
async def negotiate_start(request: Request, authorization: Optional[str] = Header(None)):
    if INCOMING_TOKEN and authorization != f"Bearer {INCOMING_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not NEGOTIATION_WEBHOOK_URL:
        raise HTTPException(status_code=500, detail="NEGOTIATION_WEBHOOK_URL not set")
    
    # print(f"start of START start")
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    print(f"Session ID is {session_id}")
    # set defaults
    entry = SESS.setdefault(session_id, {
        "status": "pending",
        "started_at": datetime.datetime.now().isoformat(),
        "request": body,  # optional: store full input
        "negotiation_history": ""   # new
    })

    # append to SESSION In memory
    entry["negotiation_history"] += (
    f"\n[User @ {datetime.datetime.now().isoformat()}] "
    f"{body.get('user_message')} "
    f"(requested_price={body.get('user_requested_price')})"
    )
    entry["status"] = "pending"
    entry["last_update"] = datetime.datetime.now().isoformat()
    entry["request"] = body
    print(f"lloads is {body.get("load")}")
    print(f"Cur round is {body.get("cur_round")}")
    print(f"Max rounds is {body.get("max_rounds")}")
    
    # make the request ot send to Happy robot negotiation workflow endpoint
    # SESS: Dict[str, Dict[str, Any]] = {}
    forward_body = {
        "event": "negotiate",
        "session_id": session_id,
        "cur_round": body.get("cur_round"),
        "load": body.get("load") or {},
        "user": {
            "message": body.get("user_message"),
            "requested_price": body.get("user_requested_price"),
        },
        "constraints": {"max_rounds": min(3, int(body.get("max_rounds") or 3)) },
        "history": entry["negotiation_history"],
    }


    headers = {"Content-Type": "application/json"}
    if NEGOTIATION_API_KEY:
        headers["X-API-Key"] = NEGOTIATION_API_KEY
    # print(f"INSIDE start")
    # fire and forget
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(NEGOTIATION_WEBHOOK_URL, json=forward_body, headers=headers)

    return {"ok": True, "session_id": session_id, "status": "negotiation started"}

@app.post("/negotiate/start/v2")
async def negotiate_start_v2_db(request: Request, authorization: Optional[str] = Header(None)):
    if INCOMING_TOKEN and authorization != f"Bearer {INCOMING_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    session_id = body.get("session_id") or str(uuid.uuid4())
    body["session_id"] = session_id  # ensure always present

    # Insert into DB
    try:
        row_id = insert_negotiation(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")

    return {
        "ok": True,
        "session_id": session_id,
        "db_id": row_id,
        "cur_round": body.get("cur_round"),
        "max_rounds": body.get("max_rounds"),
        "status": "stored"
    }


@app.post("/negotiate/result")
async def negotiate_result(request: Request, authorization: Optional[str] = Header(None)):
    """
    This is called BY HappyRobot when negotiation output is ready.
    Expecting at least: { session_id, ai_negotiated_price, ai_negotiation_reason }
    """
    if INCOMING_TOKEN and authorization != f"Bearer {INCOMING_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # Create entry if missing (idempotent)
    entry = SESS.setdefault(session_id, {
        "status": "pending",
        "started_at": datetime.datetime.now().isoformat(),
        "request": {},
        "negotiation_history": ""
    })


    entry["negotiation_history"] += (
        f"\n[AI @ {datetime.datetime.now().isoformat()}] "
        f"{body.get("ai_negotiation_reason")} "
        f"(offer=${body.get("ai_negotiated_price")})"
        )

    # Save result & mark complete
    entry["result"] = {
        "ai_negotiated_price": body.get("ai_negotiated_price"),
        "ai_negotiation_reason": body.get("ai_negotiation_reason"),
        # keep the whole body too if you want:
        # "_raw": body
    }
    entry["status"] = "complete"
    entry["last_update"] = datetime.datetime.now().isoformat()
    
    print(f"entry updated for {session_id} is {entry}")
    return {"ok": True}


@app.get("/negotiate/result/{session_id}")
async def get_negotiation_result(session_id: str):
    entry = SESS.get(session_id)
    if not entry:
        # Not created yet (or expired if you later add TTL)
        return {"ok": False, 
                "status": "unknown",
                "pending": True}

    if entry.get("status") != "complete":
        return {"ok": False, 
                "status": entry.get("status", "unknown"),
                "pending": True}

    # Return only the result in the shape your TS expects
    return {"ok": True, 
            "status": entry.get("status", "unknown"),
            "result": entry.get("result")}

@app.get("/negotiate/history/{session_id}")
async def get_negotiation_history(session_id: str, authorization: Optional[str] = Header(None)):
    if INCOMING_TOKEN and authorization != f"Bearer {INCOMING_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        rows = fetch_negotiations_by_session(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB fetch failed: {e}")

    return {"ok": True, "session_id": session_id, "history": rows}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(limit: int = Query(20, ge=1, le=100)):
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise HTTPException(500, "No database URL found")
       
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, ts, source, name, status, duration_ms, route, payload::text
                FROM events
                ORDER BY ts DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()

    # Build HTML
    html = """
    <html>
    <head>
        <title>Events Dashboard</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ccc; padding: 6px 10px; font-size: 14px; }
            th { background: #eee; }
            pre { margin: 0; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>Events Dashboard</h1>
        <table>
            <tr>
                <th>Timestamp</th><th>Source</th><th>Name</th><th>Status</th>
                <th>Duration (ms)</th><th>Route</th><th>Payload</th>
            </tr>
    """

    for r in rows:
        html += f"""
        <tr>
            <td>{r[1]}</td>
            <td>{r[2]}</td>
            <td>{r[3]}</td>
            <td>{r[4]}</td>
            <td>{r[5] or ''}</td>
            <td>{r[6] or ''}</td>
            <td><pre>{r[7] or ''}</pre></td>
        </tr>
        """

    html += "</table></body></html>"
    return HTMLResponse(content=html)

from fastapi.responses import HTMLResponse
@app.get("/negotiations_dashboard", response_class=HTMLResponse)
def negotiations_dashboard(limit: int = Query(50, ge=1, le=500)):
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise HTTPException(500, "No database URL found")
       
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, ts, session_id, load_id, miles, loadboard_rate,
                       price, user_message, user_requested_price,
                       cur_round, max_rounds,
                       ai_negotiated_price, ai_negotiated_reason, history, sentiment
                FROM negotiations
                ORDER BY ts DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()

    # Build HTML
    html = """
    <html>
    <head>
        <title>Negotiations Dashboard</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; font-size: 13px; }
            th, td { border: 1px solid #ccc; padding: 6px 10px; vertical-align: top; }
            th { background: #eee; }
            pre { margin: 0; white-space: pre-wrap; }
            details { margin: 0; }
        </style>
    </head>
    <body>
        <h1>Negotiations Dashboard</h1>
        <table>
            <tr>
                <th>ID</th><th>Timestamp</th><th>Session</th><th>Load</th>
                <th>Miles</th><th>Loadboard Rate</th><th>User Msg</th><th>User Price</th>
                <th>Round</th><th>Max Rounds</th>
                <th>AI Price</th><th>AI Reason</th><th>History</th><th>Sentiment</th>
            </tr>
    """

    for r in rows:
    
        html += f"""
        <tr>
            <td>{r[0]}</td>
            <td>{r[1]}</td>
            <td>{r[2]}</td>
            <td>{r[3]}</td>
            <td>{r[4] or ''}</td>
            <td>{r[5] or ''}</td>
            <td><pre>{r[7] or ''}</pre></td>
            <td>{r[8] or ''}</td>
            <td>{r[9]}</td>
            <td>{r[10]}</td>
            <td>{r[11] or ''}</td>
            <td><pre>{r[12] or ''}</pre></td>
            <td>{r[13]}</td>
            <td>{r[14] or ''}</td>
        </tr>
        """

    html += "</table></body></html>"
    return HTMLResponse(content=html)