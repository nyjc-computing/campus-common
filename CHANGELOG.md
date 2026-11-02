# Changelog

## 0.2.2 — 2026-11-02

- New `campus.common.services` module: the service URL registry. One
  resolver (`get_base_url` / `resolve_base_url`) owns where Campus
  services live, replacing the URL tables duplicated across
  campus.config, the campus_python SDK, and per-app resolvers.
  Resolution precedence: `CAMPUS_<SERVICE>_URL` > `<SERVICE>_URL` >
  `CAMPUS_BASE_URL` > `BASE_URL` > the per-environment `BASE_URLS`
  table. Override/base values must be bare origins and are validated
  like `PUBLIC_URL`. `get_base_url` keeps the deployment semantics
  (testing and in-process self-calls resolve to the canonical origin);
  `resolve_base_url` is the client semantics the SDK needs (no
  rewriting; `testing` resolves like development, matching the SDK's
  pre-registry behavior). Environment resolution reads `ENV` with the
  SDK's `CAMPUS_ENV` as fallback — the duality is unified here.
  Services outside the core table (e.g. `campus.profile`)
  resolve through overrides/base without registration.
- `env.py`: declared the service-URL override variables
  (`CAMPUS_BASE_URL`/`BASE_URL`, `CAMPUS_AUTH_URL`/`AUTH_URL`,
  `CAMPUS_API_URL`/`API_URL`, `CAMPUS_AUDIT_URL`/`AUDIT_URL`).

## 0.2.1 — 2026-10-28

- `utils` submodules other than `url` are now loaded lazily (module
  `__getattr__`), so a plain `import campus.common` no longer loads
  bcrypt — restores the lean-import contract guarded by the suite's
  `test_import_common_is_lean`. Public interface unchanged (same
  `__all__`; `from campus.common.utils import secret` works as before).

## 0.2.0 — 2026-10-28

First locked public-interface release. The interface is now
CI-enforced: closed-world `__all__` tests plus a checked-in manifest
(`tests/interface_manifest.json`) — an interface change is a deliberate
commit with a CHANGELOG entry and the version bump the diff dictates.

Promoted to the declared public interface (all previously worked via
undocumented submodule fallback):

- `campus.common.utils`: `uid`, `secret`, `utc_time`, `datacls`
  (`url` was already declared)
- `campus.common.errors`: `handlers` (the Flask integration surface —
  flask/werkzeug stay lazily imported, #861) and `base`
- `campus.common.validation`: `record`
- `campus.common.env`: full function/constant surface via a new
  `__all__`; the module-`__getattr__` variable lookup (`env.CLIENT_ID`)
  is documented as public interface
- `campus.common.schema`: `base`, `openapi` submodule declarations

Made private:

- `campus.common.utils.diff` → `campus.common.utils._diff` (zero
  consumers anywhere; rename, not deletion)

## 0.1.0 — 2026-10-28

Initial release: `campus.common` carved from the campus monorepo (env,
errors, introspect, schema, utils, validation). PEP 420 namespace
portion; stdlib + bcrypt only; flask stays lazy (#861).
