"""Block until the database accepts connections, so migrations don't fail on a cold start.

Run as `python -m app.wait_for_db` before `alembic upgrade head`.
"""
import os
import sys
import time

from sqlalchemy import create_engine, text

from app.database import DATABASE_URL

# Own engine with a short connect timeout so one attempt can't hang the loop
connect_args = {"connect_timeout": 3} if DATABASE_URL.startswith("postgresql") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def wait_for_db(timeout: float = float(os.getenv("DB_WAIT_TIMEOUT", "60")), interval: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Database is ready (attempt {attempt})", flush=True)
            return True
        except Exception as exc:  # driver-specific connection errors
            if time.monotonic() >= deadline:
                print(f"Database not ready after {timeout:.0f}s: {exc}", file=sys.stderr, flush=True)
                return False
            print(f"Waiting for database (attempt {attempt})...", flush=True)
            time.sleep(interval)


if __name__ == "__main__":
    sys.exit(0 if wait_for_db() else 1)
