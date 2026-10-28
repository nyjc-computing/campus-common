# campus-common

[![CI](https://github.com/nyjc-computing/campus-common/actions/workflows/ci.yml/badge.svg)](https://github.com/nyjc-computing/campus-common/actions/workflows/ci.yml)

`campus.common` — the stable shared kernel of the Campus platform:
environment handling, error types, introspection helpers, schemas, and
validation utilities.

It ships as a **PEP 420 namespace portion**: the wheel contains
`campus/common/…` with no `campus/__init__.py`, so it merges seamlessly
with the rest of the `campus` namespace installed alongside it. Runtime
dependencies: **the Python standard library + bcrypt only**, and a plain
`import campus.common` does not even load bcrypt (utils submodules load
lazily on first use).

Requires Python 3.11–3.13 (3.14 tested, unofficial).

## Installation

Consumed as a version-pinned release wheel (GitHub release asset):

```toml
[tool.poetry.dependencies]
campus-common = {url = "https://github.com/nyjc-computing/campus-common/releases/download/v0.2.1/campus_common-0.2.1-py3-none-any.whl"}
```

or directly with pip:

```bash
pip install https://github.com/nyjc-computing/campus-common/releases/download/v0.2.1/campus_common-0.2.1-py3-none-any.whl
```

PyPI publishing is planned; until then, releases live on GitHub and
consumers pin them by URL.

## Usage

Import through the shared `campus` namespace as usual — this
distribution provides the `campus.common` portion:

```python
from campus.common import env, errors, schema, utils, validation
```

| Module | Provides |
|---|---|
| `env` | environment-variable access (function + `env.VAR_NAME` attribute style), dotenv loading, deployment-environment helpers |
| `errors` | API/OAuth error taxonomy, field validation errors, Flask error handlers (flask imported lazily) |
| `introspect` | caller-module introspection helpers |
| `schema` | OpenAPI-aligned datatypes, `CampusID`/`UserID` domain aliases, shared constants |
| `utils` | `url`, `secret` (bcrypt wrappers), `uid` generation, `utc_time`, `datacls` |
| `validation` | record validation |

## Public interface

The interface is two-tier and CI-enforced:

- **Module tree** — importing submodules
  (`from campus.common.utils import url`) is supported.
- **Symbols** — public if and only if listed in the containing
  package's `__all__` (closed-world tested). Anything
  underscore-prefixed is private.

The full declared surface is snapshotted in
[`tests/interface_manifest.json`](tests/interface_manifest.json). Any
interface change is a deliberate commit: regenerate the manifest
(`python scripts/generate_interface_manifest.py`), add a CHANGELOG
entry, and bump the version per the rules below.

## Versioning

- `0.1.x`-style patches: fixes + purely additive interface growth.
- `0.2.0`-style minors: **breaking changes allowed** (strict 0.x until
  1.0). Breaking changes surface at consumers' next upgrade;
  deprecations carry a `DeprecationWarning` for one minor cycle.
- `1.0.0` = interface-stability promise; standard SemVer thereafter.

Release history: [CHANGELOG.md](CHANGELOG.md).

## Rules (CI-enforced)

- Runtime dependencies: stdlib + bcrypt only; `import campus.common`
  must stay bcrypt-free (lazy utils submodules).
- No imports of sibling `campus.*` packages — every other campus
  distribution depends on common, never the reverse
  (`tests/unit/test_boundaries.py`).
- flask/werkzeug appear only as function-level lazy imports in
  `errors/handlers.py`, which runs inside a live Flask app's error
  path. The handler tests import flask themselves (dev deps only).
- Wheels stay init-less: `poetry build` +
  `python scripts/audit_wheel_namespace.py`.

## Development

```bash
poetry install
poetry run python -m unittest discover -s tests -t .
poetry run ruff check .
poetry build && poetry run python scripts/audit_wheel_namespace.py
poetry run python scripts/generate_interface_manifest.py --check
```

`main` is protected: required checks are Ruff, Unit Tests (3.11–3.13),
and Build & Audit. Interface changes must update
`tests/interface_manifest.json` in the same PR as the CHANGELOG entry.

## Provenance

Extracted from the Campus platform monorepo
([nyjc-computing/campus](https://github.com/nyjc-computing/campus)) in
October 2026, as the first distribution of the campus-core packaging
split.
