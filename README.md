# campus-common

Skeleton for the `campus-common` distribution: the stable shared kernel of
the Campus platform, shipped as a PEP 420 namespace portion under
`campus/common`. Tracking: nyjc-computing/campus#970 (phase 3).

## Status: SKELETON — not yet installable alongside campus-suite

The real `campus.common` code still lives in the campus monorepo, whose
`campus-suite` wheel ships `campus/common/...` until the carve lands. Two
distributions shipping `campus/common` would collide (pip does not detect
overlapping file ownership between dists). Do **not** `pip install` this
package into any venv that has campus-suite installed until the carve
removes `campus/common` from campus-suite's wheel.

This skeleton exists to validate the packaging pipeline end to end:

- src layout: `src/campus/common/...` with **no** `campus/__init__.py` —
  the shared `campus/` ancestor level must stay init-less in every
  contributing distribution (rules: `docs/PACKAGING.md` in the campus
  monorepo)
- `poetry build` + `python scripts/audit_wheel_namespace.py` must pass

## Carve checklist (when the code moves)

- [ ] `git mv` `campus/common/**` from the monorepo into `src/campus/common/`
- [ ] decide `campus/config.py` home (phase-3 lean option: fold into
      `campus/common/config.py`) and update the `from campus import config`
      call sites
- [ ] campus-suite declares `campus-common` (git dep) and stops shipping
      `campus/common` in its wheel (`packages` include unchanged — the
      subtree simply moves out)
- [ ] relock all consumer dists in the same change (standing rule)
- [ ] CI: fresh-venv install smoke per dist — install built wheels of
      campus-common + campus-suite together, assert both portions resolve
      from different dists (`campus.common.__file__` vs
      `campus.model.__file__`)
