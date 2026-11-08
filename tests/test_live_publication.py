"""Offline regression tests for the existing live-publication checker.

Only read-only public route observations are covered. These tests never
authorise editorial release or classify domain renewal from DNS/HTTP.
"""

import socket
import unittest
import urllib.error
from unittest.mock import patch

from scripts import check_live_publication as checker


class RelatedIndexLineSurfaceTests(unittest.TestCase):
    def test_http_marker_is_observation_not_publication_approval(self):
        url = "https://www.mcloughlin.world/theindexline/"
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(checker, "fetch_text", return_value=(200, url, "<h1>The Index Line</h1>")),
        ):
            rows = checker.observe_related_public_surfaces((("historic_route", url),))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["address_resolution"], "RESOLVED")
        self.assertEqual(row["http_observation"], "HTTP_200_EXPECTED_MARKER_OBSERVED")
        self.assertEqual(row["registration"], "UNKNOWN")
        self.assertEqual(row["mail_mx_and_delivery"], "UNKNOWN")
        self.assertEqual(row["oncord_connection"], "UNKNOWN")
        self.assertEqual(row["editorial_approval"], "NOT_VERIFIED")
        self.assertEqual(row["publication_authorisation"], "NOT_VERIFIED")

    def test_redirect_to_unrelated_host_does_not_verify_original_route(self):
        url = "https://indexline.org/"
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(checker, "fetch_text", return_value=(200, "https://example.org/", "The Index Line")),
        ):
            row = checker.observe_related_public_surfaces((("candidate", url),))[0]
        self.assertEqual(row["http_observation"], "RESPONSE_NOT_SUFFICIENT_FOR_ROUTE_MATCH")
        self.assertEqual(row["oncord_connection"], "UNKNOWN")

    def test_failures_do_not_prove_expiry_or_change_authority(self):
        url = "https://indexline.org/"
        with (
            patch.object(checker.socket, "getaddrinfo", side_effect=socket.gaierror("lookup failed")),
            patch.object(checker, "fetch_text", side_effect=urllib.error.URLError("unavailable")),
        ):
            row = checker.observe_related_public_surfaces((("candidate", url),))[0]
        self.assertEqual(row["address_resolution"], "LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY")
        self.assertEqual(row["http_observation"], "FETCH_FAILED_NOT_PROOF_OF_DOMAIN_STATUS")
        self.assertEqual(row["registration"], "UNKNOWN")
        self.assertEqual(row["publication_authorisation"], "NOT_VERIFIED")

    def test_non_200_is_not_a_success(self):
        url = "https://indexline.org/"
        error = urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(checker, "fetch_text", side_effect=error),
        ):
            row = checker.observe_related_public_surfaces((("candidate", url),))[0]
        self.assertEqual(row["http_status"], 404)
        self.assertEqual(row["http_observation"], "HTTP_NON_200")


if __name__ == "__main__":
    unittest.main()
