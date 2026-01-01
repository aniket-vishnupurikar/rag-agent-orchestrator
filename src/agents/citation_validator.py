# src/agents/citation_validator.py
import re
from typing import List, Dict


_CITATION_PATTERN = re.compile(r"\[([A-Za-z0-9_-]+)\]")


def extract_citations(text: str) -> List[str]:
    """
    Extracts citation identifiers from model output.
    Example: [C03759]
    """
    return _CITATION_PATTERN.findall(text or "")


def validate_citations(
    assistant_text: str,
    source_map: Dict[str, dict]
) -> Dict[str, List[str]]:
    """
    Validates that cited chunk_ids exist in the source_map.

    Returns diagnostics only (non-blocking).
    """
    cited = extract_citations(assistant_text)

    valid = []
    invalid = []

    for cid in cited:
        if cid in source_map:
            valid.append(cid)
        else:
            invalid.append(cid)

    return {
        "cited": cited,
        "valid": valid,
        "invalid": invalid,
    }
