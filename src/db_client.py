from contextlib import contextmanager
import os
from typing import Any, Dict, List, Optional
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


def _connect():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(DATABASE_URL)  # your IPv4 fix can stay here if needed

def _rows_to_dicts(cur) -> List[Dict[str, Any]]:
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def search_loads(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    weight_kg: Optional[int] = None,
    miles: Optional[int] = None,
    rate_min: Optional[float] = None,
    rate_max: Optional[float] = None,
    limit: int = 10,
):
    """
    Finds loads by exact/prefix origin/destination, weight/miles tolerance, and rate bounds.
    Uses your existing columns. Returns at most `limit` rows ordered by soonest pickup, then best rate.
    """
    # tolerances (tune as you like)
    weight_tol = max(100, int((weight_kg or 0) * 0.10))
    miles_tol  = 100 

    where = []
    params: List[Any] = []

    if origin:
        # prefer exact match if user gives a full city, else allow prefix
        where.append("(lower(origin) = lower(%s) OR origin ILIKE %s || '%%')")
        params += [origin, origin]

    if destination:
        where.append("(lower(destination) = lower(%s) OR destination ILIKE %s || '%%')")
        params += [destination, destination]

    if weight_kg:
        where.append("weight BETWEEN %s AND %s")
        params += [weight_kg - weight_tol, weight_kg + weight_tol]

    if miles:
        where.append("miles BETWEEN %s AND %s")
        params += [miles - miles_tol, miles + miles_tol]

    if rate_min is not None:
        where.append("loadboard_rate IS NOT NULL AND loadboard_rate >= %s")
        params.append(rate_min)

    if rate_max is not None:
        where.append("loadboard_rate IS NOT NULL AND loadboard_rate <= %s")
        params.append(rate_max)

    where_sql = " AND ".join(where) if where else "TRUE"

    sql = f"""
        SELECT
            load_id, origin, destination, pickup_datetime, delivery_datetime,
            equipment_type, loadboard_rate, weight, commodity_type, num_of_pieces, miles, dimensions
        FROM loads
        WHERE {where_sql}
        ORDER BY pickup_datetime ASC NULLS LAST, loadboard_rate DESC NULLS LAST
        LIMIT %s
    """
    params.append(limit)

    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return _rows_to_dicts(cur)
    except Exception:
        # fail-soft so your webhook still responds
        return []