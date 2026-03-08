"""Compatibility facade for legacy imports.

Keep top-level view names stable while actual implementation lives in
feature-scoped modules under `main/features`.
"""

from .features.common.views import root, health, get_enum, get_list
from .features.installer.views import install, get_token

__all__ = [
    "root",
    "health",
    "get_enum",
    "get_list",
    "install",
    "get_token",
]
