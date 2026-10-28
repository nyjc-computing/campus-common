"""campus.common.utils

Utility functions for Campus.

Submodules other than ``url`` are loaded lazily via module-level
``__getattr__`` so that a plain ``import campus.common`` stays lean:
``url`` is pure stdlib, while ``secret`` pulls in bcrypt (the kernel's
only third-party runtime dependency) and is loaded only when hashing is
actually needed. tests/unit/common/test_import_weight.py guards this.
"""

from . import url

__all__ = ["datacls", "secret", "uid", "url", "utc_time"]


def __getattr__(name: str):
    if name in __all__ and name != "url":
        import importlib

        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
