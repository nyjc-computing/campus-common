"""Tests for the policy-mandated error-message scrubs.

Error messages are a student debug surface in production
(environment-access-policy, 2026-11-17 §4), so client-facing error
responses must not carry exception text, driver detail, or environment
values — those stay in logs (superadmin-only) and in development.

Covers:
- handle_generic_error: static message in production, exception detail
  kept in development (campus-common#8).
- handle_werkzeug_error: unknown-route 404s return the standard
  NOT_FOUND envelope, not a bare {} (campus-common#8).
- env.get_flag / services._origin_var: name-only messages, no value
  echo (campus-common#8).
"""

import json
import os
import unittest

from campus.common import env
from campus.common.errors import handlers
from campus.common.services import _origin_var

_DRIVER_TEXT = (
    "pymongo.errors.InvalidURI: mongodb://user:hunter2@db.internal:27017"
)


def _restore_env(original):
    """Restore the ENV variable the way the existing suites do."""
    if original is not None:
        os.environ["ENV"] = original
    elif "ENV" in os.environ:
        del os.environ["ENV"]


class TestGenericErrorScrub(unittest.TestCase):
    """handle_generic_error must not leak exception text in production."""

    def setUp(self):
        self.original_env = os.environ.get("ENV")

    def tearDown(self):
        _restore_env(self.original_env)

    def test_production_returns_static_message(self):
        """Production 500s carry the static message, no exception text."""
        os.environ["ENV"] = "production"
        body, status = handlers.handle_generic_error(
            ValueError(_DRIVER_TEXT)
        )
        self.assertEqual(status, 500)
        self.assertEqual(body["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn(_DRIVER_TEXT, json.dumps(body))
        self.assertNotIn("InvalidURI", json.dumps(body))

    def test_production_has_no_development_traceback(self):
        """Production 500s must not carry the development traceback."""
        os.environ["ENV"] = "production"
        body, _ = handlers.handle_generic_error(ValueError(_DRIVER_TEXT))
        self.assertNotIn("traceback", body["error"].get("details", {}))

    def test_development_keeps_exception_detail(self):
        """Development keeps the exception text for debugging."""
        os.environ["ENV"] = "development"
        body, status = handlers.handle_generic_error(
            ValueError(_DRIVER_TEXT)
        )
        self.assertEqual(status, 500)
        self.assertIn("InvalidURI", body["error"]["message"])


class TestNotFoundEnvelope(unittest.TestCase):
    """Unknown-route 404s must return the standard envelope."""

    def test_not_found_returns_envelope(self):
        import werkzeug.exceptions

        body, status = handlers.handle_werkzeug_error(
            werkzeug.exceptions.NotFound()
        )
        self.assertEqual(status, 404)
        self.assertEqual(body["error"]["code"], "NOT_FOUND")
        self.assertIn("message", body["error"])


class TestEnvValueEcho(unittest.TestCase):
    """Config error messages name the variable, never echo the value."""

    def test_get_flag_names_variable_not_value(self):
        os.environ["SOME_FLAG"] = "maybe"
        try:
            with self.assertRaises(OSError) as ctx:
                env.get_flag("SOME_FLAG")
        finally:
            del os.environ["SOME_FLAG"]
        self.assertIn("SOME_FLAG", str(ctx.exception))
        self.assertNotIn("maybe", str(ctx.exception))

    def test_origin_var_names_variable_not_value(self):
        os.environ["SOME_SERVICE_URL"] = "db.internal:27017?password=hunter2"
        try:
            with self.assertRaises(ValueError) as ctx:
                _origin_var("SOME_SERVICE_URL")
        finally:
            del os.environ["SOME_SERVICE_URL"]
        self.assertIn("SOME_SERVICE_URL", str(ctx.exception))
        self.assertNotIn("hunter2", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
