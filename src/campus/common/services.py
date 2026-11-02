"""campus.common.services

Service URL registry for Campus deployments.

One resolver owns where Campus services live, replacing the URL tables
that used to be duplicated across campus.config, the campus_python SDK,
and per-app resolvers. Services are identified by their dotted names
("campus.auth", "campus.api", "campus.audit"); apps outside the core
three (e.g. "campus.profile") resolve through the same chain without
needing a table entry, as long as an override or base URL is set.

Resolution precedence:

1. ``CAMPUS_<SERVICE>_URL`` (e.g. ``CAMPUS_AUTH_URL``) — the primary
   override, safe to name on hosts shared with non-Campus services.
2. ``<SERVICE>_URL`` (e.g. ``AUTH_URL``) — bare alias of the above,
   for dedicated hosts where the short name cannot collide.
3. ``CAMPUS_BASE_URL`` then ``BASE_URL`` — one origin fronting every
   service (gateway / single-server deployments). Callers append each
   service's route prefix (``/auth/v1``, ``/audit/v1``) themselves.
4. The per-environment ``BASE_URLS`` table (development, staging,
   production direct origins).

Override and base values must be bare origins (``scheme://host[:port]``,
no path, no trailing slash); an invalid value raises ``ValueError``
naming the variable, mirroring the ``PUBLIC_URL`` contract.

Two entry points share the chain:

- `get_base_url` — deployment semantics (what ``campus.config.get_base_url``
  has always done): in the ``testing`` environment, and for a deployment
  resolving its own name (``DEPLOY``), every service resolves to the
  canonical origin (``PUBLIC_URL``) — the cross-service test harness
  routes ``/auth``, ``/api`` and ``/audit`` path prefixes to the
  in-process Flask apps, and a service must not route to itself through
  its public URL.
- `resolve_base_url` — client semantics (what the campus_python SDK
  uses): overrides and the base URL win as configured; no testing or
  in-process rewriting, because a client library must reach the real
  services even when ``ENV=testing`` is set in its host process.

Both read the deployment environment at call time (``ENV``, with the
SDK's ``CAMPUS_ENV`` as fallback — the duality is unified here), so
processes that set it after import (e.g. test harnesses) resolve
correctly.

This module is stdlib-only and flask-free at import (the campus.common
contract, #861).
"""

__all__ = [
    "BASE_URLS",
    "get_base_url",
    "resolve_base_url",
]

from urllib.parse import urlparse

from campus.common import env
from campus.common.utils import url

# Direct per-environment service origins, used when no override or base
# URL is configured. Outer keys are service names; inner keys are
# campus.common.env deployment environments.
BASE_URLS: dict[str, dict[str, str]] = {
    "campus.auth": {
        env.DEVELOPMENT: "https://campusauth-development.up.railway.app",
        env.STAGING: "https://auth.campus.nyjc.dev",
        env.PRODUCTION: "https://auth.campus.nyjc.app",
    },
    "campus.api": {
        env.DEVELOPMENT: "https://campusapi-development.up.railway.app",
        env.STAGING: "https://api.campus.nyjc.dev",
        env.PRODUCTION: "https://api.campus.nyjc.app",
    },
    "campus.audit": {
        env.DEVELOPMENT: "https://campusaudit-development.up.railway.app",
        env.STAGING: "https://audit.campus.nyjc.dev",
        env.PRODUCTION: "https://audit.campus.nyjc.app",
    },
}

# Fallback variables applied to every service, in precedence order.
_BASE_URL_VARS = ("CAMPUS_BASE_URL", "BASE_URL")


def _origin_var(varname: str) -> str | None:
    """Read ``varname`` and validate it as a bare origin.

    Returns None when the variable is unset or empty; raises ValueError
    naming the variable when it is set but malformed.
    """
    value = env.get(varname)
    if not value:
        return None
    parse_result = urlparse(value)
    if not parse_result.scheme or not parse_result.netloc:
        raise ValueError(
            f"{varname} must be a full origin (scheme://host[:port]), "
            f"got {value!r}"
        )
    if any((
            parse_result.path,
            parse_result.params,
            parse_result.query,
            parse_result.fragment,
    )):
        raise ValueError(
            f"{varname} must be a bare origin with no path or trailing "
            f"slash, got {value!r}"
        )
    return f"{parse_result.scheme}://{parse_result.netloc}"


def resolve_base_url(
        app_name: str,
        *,
        canonical_in_testing: bool = False,
        self_canonical: bool = False,
) -> str:
    """Resolve the base URL (bare origin) for a Campus service.

    Args:
        app_name: Service name (e.g. "campus.auth", "campus.api",
            "campus.audit"). Names outside BASE_URLS resolve through
            overrides or the base URL only.
        canonical_in_testing: Resolve every service to the canonical
            origin when ``ENV=testing`` (deployment/harness semantics).
        self_canonical: Resolve a deployment to the canonical origin
            when it asks for its own name via ``DEPLOY`` — a service
            must not route to itself through its public URL.

    Returns:
        str: Bare origin (scheme://host[:port]) serving the service.

    Raises:
        ValueError: If no override or base URL is set and the service
            has no entry for the current environment, or if a set
            override/base variable is not a bare origin.
    """
    app_env = env.get("ENV", env.get("CAMPUS_ENV", env.DEVELOPMENT))
    if canonical_in_testing and app_env == env.TESTING:
        return url.canonical_origin()
    if self_canonical and env.get("DEPLOY") == app_name:
        return url.canonical_origin()

    short = app_name.removeprefix("campus.").upper()
    for varname in (
            f"CAMPUS_{short}_URL",
            f"{short}_URL",
            *_BASE_URL_VARS,
    ):
        origin = _origin_var(varname)
        if origin:
            return origin

    tier = BASE_URLS.get(app_name)
    if tier is None:
        raise ValueError(
            f"No base URL registered for service: {app_name} "
            f"(set CAMPUS_{short}_URL or CAMPUS_BASE_URL, or add it "
            f"to BASE_URLS)"
        )
    if app_env not in tier:
        raise ValueError(
            f"No base URL registered for service: {app_name} "
            f"in environment: {app_env}"
        )
    return tier[app_env]


def get_base_url(app_name: str) -> str:
    """Get the base URL for a service (deployment semantics).

    campus.config.get_base_url delegates here; see the module docstring
    for the resolution precedence and the testing/in-process rules this
    entry point applies.
    """
    return resolve_base_url(app_name, canonical_in_testing=True, self_canonical=True)
