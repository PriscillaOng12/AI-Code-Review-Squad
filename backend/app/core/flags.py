"""Feature flag utilities."""

from typing import Set
from .config import settings


def get_enabled_flags() -> Set[str]:
    """Return a set of enabled feature flags derived from the FEATURE_FLAGS env var."""
    import os

    flags_str = os.getenv("FEATURE_FLAGS", "")
    return {flag.strip() for flag in flags_str.split(",") if flag.strip()}
