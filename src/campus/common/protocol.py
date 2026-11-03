"""campus.common.protocol

Wire-protocol constants shared across campus services and consumers:
cookie names (with their TTLs) and HTTP header names that producers and
consumers on both sides of a request must agree on.

These are fixed protocol vocabulary, NOT configuration: values must
never vary per deployment, or services silently stop recognizing each
other's journeys and devices. Deployment-tunable counterparts (e.g. the
flask.session cookie names behind SESSION_COOKIE_NAMES) stay env-side.

This module is the single source of truth for the trace/journey/device
header names as of campus-common 0.3.1 / campus-api-python 0.5.1 — the
former lockstep mirrors in campus.flask_campus.propagation,
campus.audit.middleware.tracing and campus_python.tracing re-source
these names from here.
"""

__all__ = [
    "ACTION_JOURNEY_COOKIE",
    "ACTION_JOURNEY_COOKIE_MAX_AGE",
    "DEVICE_COOKIE",
    "DEVICE_COOKIE_MAX_AGE",
    "DEVICE_ID_HEADER",
    "JOURNEY_COOKIE",
    "JOURNEY_COOKIE_MAX_AGE",
    "JOURNEY_ID_HEADER",
    "JOURNEY_NAME_HEADER",
    "PARENT_SPAN_ID_HEADER",
    "TRACE_ID_HEADER",
]

# Browser login-journey correlation (#803). campus.auth sets this opaque
# cookie at the first browser touch of the login flow (GET /authorize);
# the tracing middleware stamps it into span tags so a login journey can
# be viewed as one group. The final /token hop is server-to-server and
# never carries the cookie, so its handler copies the journey id from the
# auth session into flask.g for the middleware to pick up instead.
JOURNEY_COOKIE = "campus_journey"
JOURNEY_COOKIE_MAX_AGE = 1800  # seconds; ~30 min inactivity TTL

# Action-journey correlation (#828). Set by the journeys middleware
# (campus.audit.middleware.journeys) on page navigations and refreshed
# on every request with an active journey, so one user-initiated action
# episode — page load, its XHRs and form posts, and the server-to-server
# calls they spawn (joined via forwarded X-Journey-ID headers) — groups
# as one journey. Deliberately short and sliding: episodes end on idle
# expiry (or an app's fresh=True journey boundary), never spanning a
# whole session. Distinct from JOURNEY_COOKIE (login flows).
ACTION_JOURNEY_COOKIE = "campus_action_journey"
ACTION_JOURNEY_COOKIE_MAX_AGE = 600  # seconds; ~10 min idle window

# Stable device identity (#825). campus.auth sets this opaque cookie at
# GET /authorize and reuses it on every later login from the same browser
# profile, so login sessions (and their spans) can be attributed to a
# device across re-logins and across client apps. Deliberately a standalone
# cookie, NOT a flask.session key: it is device identity, not session
# state, so /auth/v1/logout's session.clear() must not clear it.
DEVICE_COOKIE = "campus_device"
# 400 days is Chrome's maximum cookie lifetime cap.
DEVICE_COOKIE_MAX_AGE = 400 * 24 * 60 * 60

# Trace-context headers (#794): X-Request-ID carries the trace id on both
# the inbound and outbound legs; X-Parent-Span-ID carries the caller's
# span id so the receiving service records its span as a child of the
# caller's.
TRACE_ID_HEADER = "X-Request-ID"
PARENT_SPAN_ID_HEADER = "X-Parent-Span-ID"

# Action-journey headers (#828/#952): forwarded so a child service's span
# joins the caller's action journey and tags the same human label.
JOURNEY_ID_HEADER = "X-Journey-ID"
JOURNEY_NAME_HEADER = "X-Journey-Name"

# Device header (#837): non-browser clients (CLIs, scripts) cannot carry
# the campus_device cookie — they present it on API calls as this header
# instead. The tracing middleware falls back to it after flask.g.device
# and before the cookie.
DEVICE_ID_HEADER = "X-Campus-Device"
