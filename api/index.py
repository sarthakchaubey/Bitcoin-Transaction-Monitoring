"""Minimal Vercel entrypoint for the Bitcoin monitoring project.

The analytical pipeline remains an offline CLI workflow in ``main.py`` and
cannot run inside a short-lived serverless request. This endpoint provides a
health check and deployment metadata; deploy the Streamlit dashboard separately.
"""

from __future__ import annotations

import json
from typing import Any


def app(environ: dict[str, Any], start_response) -> list[bytes]:
    """Return a JSON health response compatible with Vercel's Python runtime."""
    payload = {
        "service": "bitcoin-transaction-monitoring",
        "status": "ok",
        "message": "Vercel API is deployed. Run the offline pipeline separately.",
        "pipeline_command": "python main.py",
        "dashboard_command": "streamlit run dashboard/app.py",
    }
    body = json.dumps(payload).encode("utf-8")
    start_response(
        "200 OK",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]
