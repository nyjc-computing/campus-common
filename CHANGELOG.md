# Changelog

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
