# campus-common

The stable shared kernel of the Campus platform: `campus.common` — env,
errors, introspect, schema, utils, validation. Shipped as a **PEP 420
namespace portion** under `campus/`: no `campus/__init__.py` exists here
or in any other contributing distribution, so Python merges every
`campus/` directory on `sys.path` into one namespace (rules:
`docs/PACKAGING.md` in the campus monorepo).

## Installation

```toml
[tool.poetry.dependencies]
campus-common = {git = "https://github.com/nyjc-computing/campus-common.git", branch = "main"}
```

Consumers import the shared `campus` namespace as usual —
`from campus.common import utils, env` — regardless of which distribution
provides the module.

## Rules (CI-enforced)

- Runtime dependencies: stdlib + bcrypt only.
- No imports of sibling `campus.*` packages — every other campus
  distribution depends on common, never the reverse
  (`tests/unit/test_boundaries.py`).
- flask/werkzeug appear only as function-level lazy imports in
  `errors/handlers.py`, which runs inside a live Flask app's error path
  (#861). The handler tests import flask themselves (dev deps only).
- Wheels must stay init-less: `poetry build` +
  `python scripts/audit_wheel_namespace.py` (also a CI job).

Carved out of the campus monorepo 2026-10-28 (nyjc-computing/campus#970,
phase 3). Initial release: 0.1.0.
