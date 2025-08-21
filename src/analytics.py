import json
import os, time, psycopg
from typing import Any, Dict, Optional

DATABASE_URL = os.getenv("DATABASE_URL")

def log_event(*, source: str, name: str, status: Optional[str] = None,
              duration_ms: Optional[int] = None, route: Optional[str] = None,
              user_id: Optional[str] = None, agent: Optional[str] = None,
              payload: Optional[Dict[str, Any]] = None) -> None:
    print(f"Logging events wow")
    if not DATABASE_URL:
        return
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO events (source, name, status, duration_ms, route, user_id, agent, payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    source,
                    name,
                    status,
                    int(duration_ms) if duration_ms is not None else None,  # force integer or NULL
                    route,
                    user_id,
                    agent,
                    json.dumps(payload) if payload is not None else None
                ))
            conn.commit()
    except Exception as e:
        # don't crash the request path if analytics fails
        print("[analytics] log_event error:", e)

class Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self
    def __exit__(self, exc_type, exc, tb):
        self.ms = int((time.perf_counter() - self.t0) * 1000)
