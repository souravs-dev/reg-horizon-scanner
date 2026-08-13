import hashlib


def content_hash(*parts: str) -> str:
    """Deterministic hash of a clause's normalized fields, used for change detection."""
    joined = "\x1f".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
