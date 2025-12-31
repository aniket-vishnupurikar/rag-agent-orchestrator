import time
from contextlib import contextmanager

@contextmanager
def timed_block(name: str, extra: dict = None):
    start = time.perf_counter()
    yield
    duration = (time.perf_counter() - start) * 1000
    from src.observability.logger import log_event
    log_event(
        "latency",
        {
            "block": name,
            "ms": round(duration, 2),
            **(extra or {})
        }
    )
