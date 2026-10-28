# `campus.common`

The shared kernel of the Campus platform: environment handling, error
types, introspection helpers, schemas, and validation utilities.

This directory is the package source of the **campus-common**
distribution — see the repository root [README](../../../../../README.md)
for installation, the public-interface contract, CI-enforced rules, and
the versioning policy. The declared surface is snapshotted in
`tests/interface_manifest.json` at the repository root.

Subpackages:

- `env` — environment-variable access (function and `env.VAR_NAME`
  attribute style), dotenv loading, deployment-environment helpers
- `errors` — API/OAuth error taxonomy, field validation errors, and
  Flask error handlers (flask imported lazily)
- `schema` — OpenAPI-aligned datatypes and domain aliases
  (see [schema/README.md](schema/README.md))
- `utils` — `url`, `secret` (bcrypt wrappers), `uid`, `utc_time`,
  `datacls` (loaded lazily; `import campus.common` stays bcrypt-free)
- `validation` — record validation
