import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def log_event(event_type: str, payload: dict):
    log_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "payload": payload
    }
    logging.info(json.dumps(log_record))
