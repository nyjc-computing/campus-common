"""campus.common.services

Service URL resolution for Campus deployments.

Campus is deployment-agnostic: no deployment topology is baked into the
shared kernel — not origins, not environments, not service lists. Where
services live is configured entirely through the environment (one
gateway base URL and/or per-service overrides), which is the source of
truth. Everything else a consumer needs to know about a service comes
from its OpenAPI description, published at the service's standard path.

Any dotted service name resolves ("campus.auth", "campus.api",
"campus.audit", "campus.profile", ...); there is no registry of known
services to update.

Resolution precedence:

1. ``CAMPUS_<SERVICE>_URL`` (e.g. ``CAMPUS_AUTH_URL``) — the primary
   override, safe to name on hosts shared with non-Campus services.
2. ``<SERVICE>_URL`` (e.g. ``AUTH_URL``) — bare alias of the above,
   for dedicated hosts where the short name cannot collide.
3. ``CAMPUS_BASE_URL`` then ``BASE_URL`` — one origin fronting every
   service (gateway / single-server deployments). Callers append each
   service's route prefix (``/auth/v1``, ``/audit/v1``) themselves.

Override and base values must be bare origins (``scheme://host[:port]``,
no path, no trailing slash); an invalid value raises ``ValueError``
naming the variable, mirroring the ``PUBLIC_URL`` contract. An
unconfigured service is an error naming the variables to set — there is
deliberately no fallback table.

Two entry points share the chain:

- `get_base_url` — deployment semantics (what ``campus.config.get_base_url``
  has always done): in the ``testing`` environment, and for a deployment
  resolving its own name (``DEPLOY``), every service resolves to the
  canonical origin (``PUBLIC_URL``) — the cross-service test harness
  routes ``/auth``, ``/api`` and ``/audit`` path prefixes to the
  in-process Flask apps, and a service must not route to itself through
  its public URL.
- `resolve_base_url` — client semantics (what the campus_python SDK
  uses): configuration wins as set, no rewriting — a client library
  must reach the real services even when ``ENV=testing`` is set in its
  host process.

This module is stdlib-only and flask-free at import (the campus.common
contract, #861).
"""

__all__ = [
    "get_base_url",
    "resolve_base_url",
]

from urllib.parse import urlparse

from campus.common import env
from campus.common.utils import url

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
        app_name: Dotted service name (e.g. "campus.auth",
            "campus.api", "campus.profile").
        canonical_in_testing: Resolve every service to the canonical
            origin when ``ENV=testing`` (deployment/harness semantics).
        self_canonical: Resolve a deployment to the canonical origin
            when it asks for its own name via ``DEPLOY`` — a service
            must not route to itself through its public URL.

    Returns:
        str: Bare origin (scheme://host[:port]) serving the service.

    Raises:
        ValueError: If no override or base URL is configured (the
            message names the variables to set), or if a configured
            variable is not a bare origin.
    """
    if canonical_in_testing and env.get(
            "ENV", env.get("CAMPUS_ENV", env.DEVELOPMENT)
    ) == env.TESTING:
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

    raise ValueError(
        f"No base URL configured for service: {app_name} "
        f"(set CAMPUS_{short}_URL, or CAMPUS_BASE_URL / BASE_URL for "
        f"a gateway origin)"
    )


def get_base_url(app_name: str) -> str:
    """Get the base URL for a service (deployment semantics).

    campus.config.get_base_url delegates here; see the module docstring
    for the resolution precedence and the testing/in-process rules this
    entry point applies.
    """
    return resolve_base_url(app_name, canonical_in_testing=True, self_canonical=True)
