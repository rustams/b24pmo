import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


class RequestAnalyticsMiddleware:
    """
    Lightweight API telemetry collector for admin dashboard.
    Stores request events in a rolling JSONL file.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.log_path = Path(os.getenv("API_METRICS_LOG_PATH", "/tmp/b24_api_metrics.log"))
        self.max_bytes = int(os.getenv("API_METRICS_MAX_BYTES", "10485760"))  # 10 MB

    def __call__(self, request):
        started_at = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

        path = request.path or ""
        if path.startswith("/api/") and not path.startswith("/api/admin/"):
            self._append_event(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": elapsed_ms,
                }
            )

        return response

    def _append_event(self, payload: dict):
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if self.log_path.exists() and self.log_path.stat().st_size > self.max_bytes:
                rotated = self.log_path.with_suffix(".log.1")
                if rotated.exists():
                    rotated.unlink()
                self.log_path.rename(rotated)

            with self.log_path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except OSError:
            # Telemetry should never break request processing.
            return
