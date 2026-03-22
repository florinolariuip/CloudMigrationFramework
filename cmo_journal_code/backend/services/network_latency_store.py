"""
Network Latency Override Store

Allows posting a runtime override for the inter-region network latency matrix
used by the graph-based latency model. Supports TTL-based expiration.

Usage:
  from backend.services.network_latency_store import get_override, set_override, clear_override
"""
from __future__ import annotations

from typing import Dict, Tuple, Optional
import time


_override_matrix: Optional[Dict[Tuple[str, str], float]] = None
_override_set_at: Optional[float] = None
_ttl_seconds: int = 3600  # 1 hour default


def set_override(matrix: Dict[str, float] | Dict[Tuple[str, str], float], ttl_seconds: Optional[int] = None) -> None:
    """Set a new override matrix. Keys may be "from,to" strings or (from,to) tuples."""
    global _override_matrix, _override_set_at, _ttl_seconds
    normalized: Dict[Tuple[str, str], float] = {}
    for k, v in (matrix or {}).items():
        if isinstance(k, tuple) and len(k) == 2:
            key = (str(k[0]), str(k[1]))
            normalized[key] = float(v)
        elif isinstance(k, str) and "," in k:
            a, b = k.split(",", 1)
            key = (a.strip(), b.strip())
            normalized[key] = float(v)
    _override_matrix = normalized if normalized else None
    _override_set_at = time.time() if _override_matrix else None
    if ttl_seconds is not None:
        _ttl_seconds = int(ttl_seconds)


def get_override() -> Optional[Dict[Tuple[str, str], float]]:
    """Return current override matrix if not expired, else None."""
    global _override_matrix, _override_set_at
    if not _override_matrix or not _override_set_at:
        return None
    if (time.time() - _override_set_at) > _ttl_seconds:
        clear_override()
        return None
    return _override_matrix


def clear_override() -> None:
    global _override_matrix, _override_set_at
    _override_matrix = None
    _override_set_at = None


def status() -> dict:
    return {
        "has_override": _override_matrix is not None,
        "entries": len(_override_matrix) if _override_matrix else 0,
        "ttl_seconds": _ttl_seconds,
        "age_seconds": (time.time() - _override_set_at) if _override_set_at else None,
    }
