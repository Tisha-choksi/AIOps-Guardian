"""Deliberately breakable target app used as the Docker Agent's investigation
subject. Break it by either:

  docker stop sample-app          # simulates a hard-down container
  docker compose ... up -d -e CRASH_ON_START=true sample-app   # simulates a bad deploy / crash loop
"""

import os
import sys

import psycopg
from flask import Flask, jsonify

app = Flask(__name__)


def _maybe_crash_on_start() -> None:
    if os.environ.get("CRASH_ON_START", "false").lower() == "true":
        print("CRASH_ON_START is set - exiting to simulate a bad deployment", flush=True)
        sys.exit(1)


@app.route("/health")
def health():
    database_url = os.environ.get("DATABASE_URL", "")
    try:
        with psycopg.connect(database_url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return jsonify(status="ok"), 200
    except Exception as exc:
        return jsonify(status="error", detail=str(exc)), 500


if __name__ == "__main__":
    _maybe_crash_on_start()
    app.run(host="0.0.0.0", port=5000)
