import re
from typing import Optional

INTENT_PATTERNS = {
    "authentication_help": [
        "login",
        "password",
        "authentication",
        "reset",
        "access"
    ],
    "hr_policy": [
        "probation",
        "leave",
        "policy",
        "employee",
        "hr"
    ],
    "financial_insight": [
        "revenue",
        "growth",
        "financial",
        "segment",
        "fiscal"
    ],
}


def classify_intent(message: str) -> Optional[str]:
    msg = message.lower()

    for intent, keywords in INTENT_PATTERNS.items():
        for kw in keywords:
            if kw in msg:
                return intent

    return None
