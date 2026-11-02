"""Tests for campus.common.services (service URL resolution).

The resolution contract: environment variables are the source of truth
(no baked-in topology — Campus is deployment-agnostic), per-service
overrides beat the gateway base URL, and an unconfigured service is an
error naming the variables to set.
"""

import contextlib
import os
import unittest

from campus.common import env, services


class ServiceURLTestCase(unittest.TestCase):
    """Base class that isolates the process environment per test."""

    def setUp(self):
        # Resolution reads env at call time; pin and restore every
        # variable the resolver consults (CI sets ENV=testing globally,
        # so ENV is always set explicitly here and restored after).
        self.patch_env(
            ENV=env.DEVELOPMENT,
            DEPLOY="",
            PUBLIC_URL="https://gateway.example",
            CAMPUS_AUTH_URL="",
            AUTH_URL="",
            CAMPUS_API_URL="",
            API_URL="",
            CAMPUS_AUDIT_URL="",
            AUDIT_URL="",
            CAMPUS_BASE_URL="",
            BASE_URL="",
            CAMPUS_ENV="",
        )

    def patch_env(self, **values):
        """Set env vars for the test, restoring the previous values after."""
        for name, value in values.items():
            previous = os.environ.get(name)
            env.set(name, value)
            if previous is None:
                self.addCleanup(self._delete_quietly, name)
            else:
                self.addCleanup(env.set, name, previous)

    @staticmethod
    def _delete_quietly(name):
        with contextlib.suppress(KeyError):
            env.delete(name)


class TestResolutionPrecedence(ServiceURLTestCase):
    """CAMPUS_<S>_URL > <S>_URL > CAMPUS_BASE_URL > BASE_URL."""

    def test_prefixed_override_wins(self):
        self.patch_env(
            CAMPUS_AUTH_URL="https://auth-primary.example",
            AUTH_URL="https://auth-bare.example",
            BASE_URL="https://base.example",
        )
        self.assertEqual(
            services.get_base_url("campus.auth"),
            "https://auth-primary.example",
        )

    def test_bare_override_beats_base(self):
        self.patch_env(
            AUTH_URL="https://auth-bare.example",
            CAMPUS_BASE_URL="https://base.example",
        )
        self.assertEqual(
            services.get_base_url("campus.auth"),
            "https://auth-bare.example",
        )

    def test_prefixed_base_beats_bare_base(self):
        self.patch_env(
            CAMPUS_BASE_URL="https://base-prefixed.example",
            BASE_URL="https://base-bare.example",
        )
        self.assertEqual(
            services.get_base_url("campus.api"),
            "https://base-prefixed.example",
        )

    def test_base_url_applies_to_every_service(self):
        self.patch_env(BASE_URL="https://base.example")
        for app_name in ("campus.auth", "campus.api", "campus.audit"):
            self.assertEqual(
                services.get_base_url(app_name), "https://base.example"
            )

    def test_base_url_supports_non_core_services(self):
        self.patch_env(CAMPUS_PROFILE_URL="https://profile.example")
        self.assertEqual(
            services.resolve_base_url("campus.profile"),
            "https://profile.example",
        )


class TestNoBakedInTopology(ServiceURLTestCase):
    """Unconfigured services error; there is no fallback table."""

    def test_unconfigured_service_errors_naming_the_vars(self):
        with self.assertRaisesRegex(ValueError, "CAMPUS_AUTH_URL"):
            services.get_base_url("campus.auth")

    def test_unconfigured_in_testing_still_errors_for_clients(self):
        # Client semantics: testing never rewrites, and never invents a URL.
        self.patch_env(ENV=env.TESTING)
        with self.assertRaisesRegex(ValueError, "CAMPUS_AUDIT_URL"):
            services.resolve_base_url("campus.audit")

    def test_error_message_suggests_base_url(self):
        with self.assertRaisesRegex(ValueError, "CAMPUS_BASE_URL"):
            services.get_base_url("campus.profile")


class TestDeploymentSemantics(ServiceURLTestCase):
    """get_base_url rewrites to the canonical origin for harness/self."""

    def test_testing_resolves_canonical_origin(self):
        self.patch_env(ENV=env.TESTING, BASE_URL="https://base.example")
        self.assertEqual(
            services.get_base_url("campus.auth"),
            "https://gateway.example",
        )

    def test_testing_canonical_beats_overrides(self):
        self.patch_env(
            ENV=env.TESTING,
            CAMPUS_AUTH_URL="https://auth-primary.example",
        )
        self.assertEqual(
            services.get_base_url("campus.auth"),
            "https://gateway.example",
        )

    def test_self_deployment_resolves_canonical_origin(self):
        self.patch_env(DEPLOY="campus.audit", BASE_URL="https://base.example")
        self.assertEqual(
            services.get_base_url("campus.audit"),
            "https://gateway.example",
        )
        # Another service still resolves through the chain.
        self.assertEqual(
            services.get_base_url("campus.auth"),
            "https://base.example",
        )


class TestClientSemantics(ServiceURLTestCase):
    """resolve_base_url (SDK semantics) never rewrites to canonical."""

    def test_testing_does_not_canonicalize(self):
        self.patch_env(ENV=env.TESTING, BASE_URL="https://base.example")
        self.assertEqual(
            services.resolve_base_url("campus.auth"),
            "https://base.example",
        )

    def test_self_deployment_does_not_canonicalize(self):
        self.patch_env(DEPLOY="campus.audit", BASE_URL="https://base.example")
        self.assertEqual(
            services.resolve_base_url("campus.audit"),
            "https://base.example",
        )


class TestOriginValidation(ServiceURLTestCase):
    """Override/base values must be bare origins; errors name the var."""

    def test_scheme_less_value_rejected(self):
        self.patch_env(CAMPUS_AUTH_URL="campusauth.example")
        with self.assertRaisesRegex(ValueError, "CAMPUS_AUTH_URL"):
            services.get_base_url("campus.auth")

    def test_path_component_rejected(self):
        self.patch_env(BASE_URL="https://base.example/gateway")
        with self.assertRaisesRegex(ValueError, "BASE_URL"):
            services.get_base_url("campus.auth")

    def test_trailing_slash_rejected(self):
        self.patch_env(AUTH_URL="https://auth.example/")
        with self.assertRaisesRegex(ValueError, "AUTH_URL"):
            services.get_base_url("campus.auth")

    def test_invalid_prefixed_override_fails_even_if_alias_valid(self):
        self.patch_env(
            CAMPUS_AUTH_URL="not-an-origin",
            AUTH_URL="https://auth-bare.example",
        )
        with self.assertRaisesRegex(ValueError, "CAMPUS_AUTH_URL"):
            services.get_base_url("campus.auth")

    def test_origin_normalization(self):
        self.patch_env(CAMPUS_AUTH_URL="https://auth.example:8443")
        self.assertEqual(
            services.get_base_url("campus.auth"),
            "https://auth.example:8443",
        )


if __name__ == "__main__":
    unittest.main()
