


import os
from pathlib import Path
from psycopg import sql as psql
import psycopg

INIT_DIR_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "db" / "init",  # /app/src -> /app/db/init
    Path("/app/db/init"),                                    # explicit path (Fly image)
]

def find_init_dir() -> Path:
    for p in INIT_DIR_CANDIDATES:
        if p.exists():
            return p
    raise SystemExit("Could not find db/init directory in the image.")

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("Database URL not found!")
    
    init_dir = find_init_dir()
    sql_files = sorted(init_dir.glob("*.sql"))
    if not sql_files:
        raise SystemExit(f"No .sql files found in {init_dir}")
    
    print(f"[migrate] Using DATABASE_URL={db_url.split('@')[-1]} (redacted user/pass)")
    print(f"[migrate] Applying {len(sql_files)} file(s) from {init_dir}")

    # Connect and run files one-by-one (transaction per file)
    with psycopg.connect(db_url) as conn:
        for f in sql_files:
            sql = f.read_text(encoding="utf-8")
            print(f"[migrate] -> {f.name} ({len(sql)} bytes)")
            try:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(psql.SQL(sql))# type: ignore[arg-type]
                print(f"[migrate] OK  {f.name}")
            except Exception as e:
                # Don’t fail the whole deploy for harmless extension errors, etc.
                print(f"[migrate] WARN {f.name}: {e}")

    print("[migrate] Done.")

if __name__ == "__main__":
    main()