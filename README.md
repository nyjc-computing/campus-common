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
- The public interface is locked: package `__all__`s are closed-world
  tested and `tests/interface_manifest.json` snapshots the declared
  surface (`scripts/generate_interface_manifest.py --check`).
  Interface changes ship with a CHANGELOG entry and the version bump
  the diff dictates — additive → patch, breaking → minor (pre-1.0
  minors may break).

## Versioning

- `0.1.x` patches: fixes + purely additive interface growth.
- `0.2.0`-style minors: **breaking changes allowed** (strict 0.x —
  treat minors as majors until 1.0). Breaking changes surface loudly at
  every consumer's next relock; deprecations get a
  `DeprecationWarning` one minor cycle before removal.
- `1.0.0` = interface-stability promise; standard SemVer thereafter.

Carved out of the campus monorepo 2026-10-28 (nyjc-computing/campus#970,
phase 3). Initial release: 0.1.0.
