from contextlib import contextmanager
import os
from typing import Any, Dict, List
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    with psycopg.connect(DATABASE_URL) as conn:
        yield conn

def fetch_recent_loads(limit: int = 10) -> list[dict[str, Any]]:
    sql = """
        SELECT load_id, origin, destination, pickup_datetime, delivery_datetime,
             equipment_type, loadboard_rate, notes, weight, commodity_type,
             num_of_pieces, miles, dimensions
      FROM loads
      ORDER BY pickup_datetime DESC
      LIMIT %s
"""
    cols = ["load_id","origin","destination","pickup_datetime","delivery_datetime",
            "equipment_type","loadboard_rate","notes","weight","commodity_type",
            "num_of_pieces","miles","dimensions"]
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
    out = []
    for r in rows:
        item = {c: v for c, v in zip(cols, r)}
        if item["pickup_datetime"] : item["pickup_datetime"]   = item["pickup_datetime"].isoformat()
        if item["delivery_datetime"]: item["delivery_datetime"] = item["delivery_datetime"].isoformat()
        out.append(item)
    return out

def find_closest_by_weight(target_kg: int, limit: int = 5) -> list[dict[str, Any]]:
    sql = """
      SELECT load_id, origin, destination, weight, equipment_type, loadboard_rate
      FROM loads
      WHERE weight IS NOT NULL
      ORDER BY ABS(weight - %s)
      LIMIT %s
    """
    cols = ["load_id","origin","destination","weight","equipment_type","loadboard_rate"]
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (target_kg, limit))
        rows = cur.fetchall()
    return [{c: v for c, v in zip(cols, r)} for r in rows]