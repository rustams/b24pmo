def sync_status_payload() -> dict:
    return {
        "module": "sync.status",
        "status": "scaffolded",
        "next": "Expose sync_log status and worker lag metrics",
    }


def run_initial_sync_payload() -> dict:
    return {
        "module": "sync.initial",
        "status": "queued",
        "next": "Connect to queue worker and execute idempotent initial sync",
    }
